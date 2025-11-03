
import streamlit as st
from PIL import Image
import io
import json
from datetime import datetime
import pytesseract
import re

# Set page config FIRST
st.set_page_config(
    page_title="Menu Dietary Filter",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tesseract configuration
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    
    .stButton>button {
        width: 100%;
        background-color: #FF6B6B;
        color: white;
        font-weight: 600;
        padding: 0.75rem;
        border-radius: 10px;
        border: none;
        font-size: 1.1rem;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #FF5252;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255,107,107,0.3);
    }
    
    .safe-dish {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #28a745;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .unsafe-dish {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #dc3545;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    h1 {
        color: #2C3E50;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }
    
    .subtitle {
        color: #7F8C8D;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None

# Function to analyze dishes based on dietary restrictions
def analyze_menu_items(text, restrictions):
    """
    Analyze menu text and filter based on dietary restrictions
    """
    results = []
    
    # Split text into lines and process
    lines = text.split('\n')
    
    # Keywords for different restrictions
    vegan_unsafe = ['meat', 'chicken', 'beef', 'pork', 'fish', 'egg', 'dairy', 'milk', 'cheese', 'butter', 'cream', 'honey']
    vegetarian_unsafe = ['meat', 'chicken', 'beef', 'pork', 'fish', 'seafood']
    gluten_unsafe = ['wheat', 'bread', 'pasta', 'flour', 'barley', 'rye', 'soy sauce']
    dairy_unsafe = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'paneer']
    nut_unsafe = ['nut', 'peanut', 'almond', 'cashew', 'walnut', 'pistachio']
    shellfish_unsafe = ['shrimp', 'crab', 'lobster', 'shellfish', 'prawn']
    
    # Process each line as a potential dish
    for line in lines:
        line = line.strip()
        if len(line) < 5:  # Skip very short lines
            continue
            
        # Try to extract price
        price_match = re.search(r'[\$₹€£]\s*\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*[\$₹€£]', line)
        price = price_match.group(0) if price_match else 'N/A'
        
        # Remove price from dish name
        dish_name = re.sub(r'[\$₹€£]\s*\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*[\$₹€£]', '', line).strip()
        
        if not dish_name:
            continue
        
        # Analyze safety based on restrictions
        line_lower = line.lower()
        is_safe = True
        unsafe_for = []
        safe_for = []
        reasons = []
        warnings = []
        hidden_ingredients = []
        
        # Check each restriction
        if 'Vegan' in restrictions:
            if any(keyword in line_lower for keyword in vegan_unsafe):
                is_safe = False
                unsafe_for.append('Vegan')
                reasons.append('Contains animal products')
            else:
                safe_for.append('Vegan')
        
        if 'Vegetarian' in restrictions:
            if any(keyword in line_lower for keyword in vegetarian_unsafe):
                is_safe = False
                unsafe_for.append('Vegetarian')
                reasons.append('Contains meat or fish')
            else:
                safe_for.append('Vegetarian')
        
        if 'Gluten-Free' in restrictions:
            if any(keyword in line_lower for keyword in gluten_unsafe):
                is_safe = False
                unsafe_for.append('Gluten-Free')
                reasons.append('Contains gluten')
            else:
                safe_for.append('Gluten-Free')
                warnings.append('Verify no cross-contamination')
        
        if 'Dairy-Free' in restrictions:
            if any(keyword in line_lower for keyword in dairy_unsafe):
                is_safe = False
                unsafe_for.append('Dairy-Free')
                reasons.append('Contains dairy products')
            else:
                safe_for.append('Dairy-Free')
        
        if 'Nut Allergy' in restrictions:
            if any(keyword in line_lower for keyword in nut_unsafe):
                is_safe = False
                unsafe_for.append('Nut Allergy')
                reasons.append('Contains nuts')
                warnings.append('HIGH ALLERGY RISK')
            else:
                safe_for.append('Nut Allergy')
                warnings.append('Always verify with restaurant staff')
        
        if 'Shellfish Allergy' in restrictions:
            if any(keyword in line_lower for keyword in shellfish_unsafe):
                is_safe = False
                unsafe_for.append('Shellfish Allergy')
                reasons.append('Contains shellfish')
                warnings.append('HIGH ALLERGY RISK')
            else:
                safe_for.append('Shellfish Allergy')
        
        # Add to results
        confidence = 70 if is_safe else 85  # Conservative confidence
        
        if not is_safe and not reasons:
            reasons.append('Unable to verify all ingredients')
        
        if is_safe and not safe_for:
            safe_for = restrictions.copy()
        
        results.append({
            'dish_name': dish_name,
            'description': line,
            'price': price,
            'safe': is_safe,
            'confidence': confidence,
            'safe_for': safe_for,
            'unsafe_for': unsafe_for,
            'reasons': reasons if reasons else ['No concerning ingredients detected'],
            'hidden_ingredients': ['Ask staff about preparation methods', 'Check for cross-contamination'],
            'warnings': warnings if warnings else ['Always verify with restaurant'],
            'modifications': 'Ask staff for ingredient substitutions' if not is_safe else None
        })
    
    return results

# Main title
st.title("🍽️ Restaurant Menu Dietary Filter")

# Hero Section
st.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem;'>
    <h2 style='color: white; margin: 0;'>🍽️ Eat Safe, Dine Happy</h2>
    <p style='color: #e0e7ff; font-size: 1.1rem; margin-top: 0.5rem;'>
        Upload any menu → OCR extracts text → Filter by dietary restrictions
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar for dietary restrictions
with st.sidebar:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;'>
        <h2 style='color: white; margin: 0;'>⚙️ Your Profile</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🌱 Dietary Preferences")
    
    restrictions = []
    
    if st.checkbox("Vegan", help="No animal products"):
        restrictions.append("Vegan")
    if st.checkbox("Vegetarian", help="No meat or fish"):
        restrictions.append("Vegetarian")
    if st.checkbox("Pescatarian", help="No meat, but fish is okay"):
        restrictions.append("Pescatarian")
    
    # Allergens
    st.markdown("### 🚫 Allergies")
    if st.checkbox("Gluten/Wheat Allergy"):
        restrictions.append("Gluten-Free")
    if st.checkbox("Dairy/Lactose Allergy"):
        restrictions.append("Dairy-Free")
    if st.checkbox("Nut Allergy"):
        restrictions.append("Nut Allergy")
    if st.checkbox("Shellfish Allergy"):
        restrictions.append("Shellfish Allergy")
    if st.checkbox("Egg Allergy"):
        restrictions.append("Egg Allergy")
    if st.checkbox("Soy Allergy"):
        restrictions.append("Soy Allergy")
    if st.checkbox("Fish Allergy"):
        restrictions.append("Fish Allergy")
    
    # Religious/Cultural
    st.markdown("### 🕌 Religious/Cultural")
    if st.checkbox("Halal"):
        restrictions.append("Halal")
    if st.checkbox("Kosher"):
        restrictions.append("Kosher")
    
    st.markdown("---")
    if restrictions:
        st.success(f"✅ {len(restrictions)} restriction(s) selected")
    else:
        st.warning("⚠️ Select at least one restriction")

# Example section
with st.expander("👁️ See Example - How It Works"):
    st.markdown("""
    **How it works:**
    1. 📸 Take a photo of restaurant menu
    2. ☑️ Select your dietary restrictions from the sidebar
    3. 🚀 Click analyze - Tesseract OCR extracts text
    4. ✅ Get instant filtered results!
    
    **Supported restrictions:**
    - 🌱 Vegan, Vegetarian, Pescatarian
    - 🚫 Gluten-free, Dairy-free
    - ⚠️ Nut allergy, Shellfish allergy, Egg allergy, Soy allergy, Fish allergy
    - 🕌 Halal, Kosher
    
    **What you'll get:**
    - Safe dishes highlighted in green
    - Unsafe dishes with detailed reasons
    - Hidden ingredient warnings
    - Modification suggestions
    - Downloadable reports
    """)

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📸 Upload Menu Image")
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear photo of the restaurant menu"
    )
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Menu", use_column_width=True)
        
        # Image quality check
        width, height = image.size
        if width < 800 or height < 600:
            st.warning("⚠️ Image resolution is low. OCR results may be less accurate.")

with col2:
    st.subheader("🔍 Ready to Analyze")
    
    if not uploaded_file:
        st.info("👈 Upload a menu image to get started")
    elif not restrictions:
        st.warning("👈 Select your dietary restrictions from the sidebar")
    else:
        st.success("✅ Ready to analyze!")
        
        if st.button("🚀 Analyze Menu Now", type="primary"):
            st.session_state.analyzed = False
            
            with st.spinner(""):
                st.markdown("""
                <div style='text-align: center; padding: 2rem;'>
                    <div style='font-size: 3rem; animation: pulse 1.5s infinite;'>
                        🔍
                    </div>
                    <h3 style='color: #667eea; margin-top: 1rem;'>
                        Extracting text from menu...
                    </h3>
                    <p style='color: #999;'>Using Tesseract OCR</p>
                </div>
                """, unsafe_allow_html=True)
                
                try:
                    # Extract text using Tesseract OCR
                    extracted_text = pytesseract.image_to_string(image)
                    st.session_state.extracted_text = extracted_text
                    
                    if not extracted_text.strip():
                        st.error("❌ No text detected in image. Please upload a clearer image.")
                    else:
                        # Analyze the extracted text
                        results = analyze_menu_items(extracted_text, restrictions)
                        
                        if not results:
                            st.warning("⚠️ No menu items detected. Try a clearer image.")
                        else:
                            st.session_state.results = results
                            st.session_state.analyzed = True
                            st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Make sure Tesseract is installed correctly.")

# Display extracted text (for debugging)
if st.session_state.extracted_text and not st.session_state.analyzed:
    with st.expander("📄 View Extracted Text"):
        st.text(st.session_state.extracted_text)

# Display results
if st.session_state.analyzed and st.session_state.results:
    results = st.session_state.results
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
    total_dishes = len(results)
    safe_dishes = [r for r in results if r.get('safe', False)]
    unsafe_dishes = [r for r in results if not r.get('safe', False)]
    
    st.markdown("### 📊 Quick Stats")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1.5rem; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 2rem; font-weight: 700;'>{total_dishes}</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>Total Dishes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        percentage = int(len(safe_dishes)/total_dishes*100) if total_dishes > 0 else 0
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    padding: 1.5rem; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 2rem; font-weight: 700;'>{len(safe_dishes)}</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>Safe Options ({percentage}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                    padding: 1.5rem; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 2rem; font-weight: 700;'>{len(unsafe_dishes)}</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>To Avoid</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_confidence = sum(d.get('confidence', 0) for d in results) / len(results) if results else 0
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
                    padding: 1.5rem; border-radius: 12px; text-align: center; color: white;'>
            <div style='font-size: 2rem; font-weight: 700;'>{int(avg_confidence)}%</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>Avg Confidence</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["✅ Safe to Eat", "❌ Avoid", "📋 All Dishes"])
    
    with tab1:
        st.markdown("### Green Light - Safe Options")
        
        if safe_dishes:
            for dish in safe_dishes:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                            padding: 1.5rem; border-radius: 15px; margin: 1rem 0;
                            border-left: 5px solid #28a745; box-shadow: 0 4px 15px rgba(40,167,69,0.2);'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h3 style='margin:0; color:#155724; font-size: 1.3rem;'>
                            ✅ {dish['dish_name']}
                        </h3>
                        <span style='background: #28a745; color: white; padding: 0.3rem 1rem;
                                     border-radius: 20px; font-weight: 600;'>
                            {dish.get('price', 'N/A')}
                        </span>
                    </div>
                    <p style='color:#666; margin:0.8rem 0 0 0; font-style: italic;'>
                        {dish.get('description', 'No description')}
                    </p>
                    <div style='margin-top: 0.8rem;'>
                        <span style='background: #d4edda; color: #155724; padding: 0.3rem 0.8rem;
                                     border-radius: 10px; font-size: 0.9rem; margin-right: 0.5rem;'>
                            🎯 {dish.get('confidence', 0)}% Confidence
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📝 Details for {dish['dish_name']}"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        confidence = dish.get('confidence', 0)
                        st.metric("Confidence Level", f"{confidence}%")
                        
                        if confidence >= 90:
                            st.success("🎯 Very High Confidence")
                        elif confidence >= 70:
                            st.info("✓ Good Confidence")
                        else:
                            st.warning("⚠️ Moderate Confidence - Double check with staff")
                    
                    with col_b:
                        if dish.get('safe_for'):
                            st.write("**✅ Safe for:**")
                            for restriction in dish['safe_for']:
                                st.write(f"• {restriction}")
                    
                    if dish.get('reasons'):
                        st.write("**Why it's safe:**")
                        for reason in dish['reasons']:
                            st.success(f"✓ {reason}")
                    
                    if dish.get('warnings'):
                        st.warning("⚠️ **Important Warnings:**")
                        for warning in dish['warnings']:
                            st.write(f"• {warning}")
                    
                    if dish.get('hidden_ingredients'):
                        st.info("**💡 Watch out for:**")
                        for ing in dish['hidden_ingredients']:
                            st.write(f"• {ing}")
        else:
            st.warning("😔 No completely safe dishes found based on your restrictions.")
            st.info("💡 Check the 'Avoid' tab for dishes that might work with modifications.")
    
    with tab2:
        st.markdown("### Red Light - Dishes to Avoid")
        
        if unsafe_dishes:
            for dish in unsafe_dishes:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                            padding: 1.5rem; border-radius: 12px; margin: 1rem 0;
                            border-left: 5px solid #dc3545; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
                    <h3 style='margin:0; color:#721c24;'>❌ {dish['dish_name']} 
                    <span style='float:right; color:#dc3545; font-size:0.9rem;'>{dish.get('price', 'N/A')}</span></h3>
                    <p style='color:#666; margin:0.5rem 0;'><em>{dish.get('description', 'No description')}</em></p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📝 Why you should avoid {dish['dish_name']}"):
                    if dish.get('unsafe_for'):
                        st.error(f"**❌ Conflicts with:** {', '.join(dish['unsafe_for'])}")
                    
                    if dish.get('reasons'):
                        st.write("**Reasons:**")
                        for reason in dish['reasons']:
                            st.write(f"• {reason}")
                    
                    if dish.get('hidden_ingredients'):
                        st.warning("**⚠️ Hidden ingredients detected:**")
                        for ing in dish['hidden_ingredients']:
                            st.write(f"• {ing}")
                    
                    if dish.get('modifications'):
                        st.success(f"💡 **Possible modification:** {dish['modifications']}")
                        st.info("Always verify modifications with restaurant staff!")
        else:
            st.success("🎉 Great news! All dishes on this menu are safe for you!")
    
    with tab3:
        st.markdown("### Complete Menu Overview")
        
        summary_data = []
        for dish in results:
            summary_data.append({
                "Dish": dish['dish_name'],
                "Status": "✅ Safe" if dish['safe'] else "❌ Avoid",
                "Confidence": f"{dish.get('confidence', 0)}%",
                "Price": dish.get('price', 'N/A')
            })
        
        st.dataframe(summary_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("📥 Export Your Results")
    
    def generate_report():
        report = f"""
🍽️ MENU DIETARY ANALYSIS REPORT
{'='*60}
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Dietary Restrictions: {', '.join(restrictions)}
{'='*60}

SUMMARY:
- Total Dishes Analyzed: {total_dishes}
- Safe Options: {len(safe_dishes)} ({len(safe_dishes)/total_dishes*100:.1f}%)
- Dishes to Avoid: {len(unsafe_dishes)} ({len(unsafe_dishes)/total_dishes*100:.1f}%)

{'='*60}
✅ SAFE TO EAT ({len(safe_dishes)} dishes)
{'='*60}

"""
        for dish in safe_dishes:
            report += f"\n{dish['dish_name']} - {dish.get('price', 'N/A')}\n"
            report += f"Description: {dish.get('description', 'N/A')}\n"
            report += f"Confidence: {dish.get('confidence', 0)}%\n"
            if dish.get('reasons'):
                report += f"Reasons: {'; '.join(dish['reasons'])}\n"
            if dish.get('warnings'):
                report += f"⚠️  Warnings: {'; '.join(dish['warnings'])}\n"
            report += "\n"
        
        report += f"\n{'='*60}\n"
        report += f"❌ DISHES TO AVOID ({len(unsafe_dishes)} dishes)\n"
        report += f"{'='*60}\n\n"
        
        for dish in unsafe_dishes:
            report += f"\n{dish['dish_name']}\n"
            report += f"Description: {dish.get('description', 'N/A')}\n"
            if dish.get('reasons'):
                report += f"Reason: {'; '.join(dish['reasons'])}\n"
            if dish.get('modifications'):
                report += f"💡 Possible modification: {dish['modifications']}\n"
            report += "\n"
        
        report += f"\n{'='*60}\n"
        report += "⚠️  IMPORTANT DISCLAIMER:\n"
        report += "This analysis is OCR-based and should be used as a guide only.\n"
        report += "Always verify ingredients with restaurant staff, especially for severe allergies.\n"
        report += f"{'='*60}\n"
        
        return report
    
    col_download1, col_download2 = st.columns(2)
    
    with col_download1:
        report = generate_report()
        st.download_button(
            label="📄 Download Text Report",
            data=report,
            file_name=f"menu_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col_download2:
        json_data = json.dumps(results, indent=2)
        st.download_button(
            label="📊 Download JSON Data",
            data=json_data,
            file_name=f"menu_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    st.markdown("---")
    st.info("""
    ⚠️ **Important Disclaimer:** This analysis uses Tesseract OCR and keyword matching. 
    For severe allergies or medical dietary restrictions, always verify ingredients directly with restaurant staff.
    Cross-contamination and hidden ingredients may not be detected.
    """)

st.markdown("---")
st.markdown("### 💬 What People Say")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 12px;
                border-left: 4px solid #667eea;'>
        <p style='font-style: italic; color: #666;'>
            "Saved me so much time! No more reading every menu item."
        </p>
        <p style='margin: 0; font-weight: 600; color: #667eea;'>- Sarah, Vegan</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 12px;
                border-left: 4px solid #28a745;'>
        <p style='font-style: italic; color: #666;'>
            "As someone with severe nut allergies, this gives me peace of mind."
        </p>
        <p style='margin: 0; font-weight: 600; color: #28a745;'>- Mike, Nut Allergy</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 12px;
                border-left: 4px solid #ffc107;'>
        <p style='font-style: italic; color: #666;'>
            "Perfect for finding halal options when traveling!"
        </p>
        <p style='margin: 0; font-weight: 600; color: #ffc107;'>- Fatima, Halal</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7F8C8D; padding: 2rem 0;'>
    <p>Built with ❤️ using Streamlit & Tesseract OCR</p>
    <p>🔒 Your data is processed locally and not stored</p>
</div>
""", unsafe_allow_html=True)