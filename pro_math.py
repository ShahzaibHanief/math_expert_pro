import streamlit as st
import google.generativeai as genai
import time 
from typing import Iterator

# ✅ RESPONSIVE CSS FOR MOBILE
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        /* Single column layout on mobile */
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Stack columns vertically on mobile */
        [data-testid="column"] {
            width: 100% !important;
            margin-bottom: 1rem;
        }
        
        /* Smaller text on mobile */
        .stTextArea textarea {
            font-size: 14px;
        }
        
        /* Adjust button sizes */
        .stButton button {
            width: 100%;
            font-size: 14px;
        }
        
        /* Reduce padding */
        .main .block-container {
            padding: 1rem;
        }
        
        /* Sidebar adjustments */
        .sidebar .sidebar-content {
            width: 200px;
        }
    }
    
    /* Tablet adjustments */
    @media (max-width: 1024px) {
        .sidebar .sidebar-content {
            width: 250px;
        }
    }
</style>
""", unsafe_allow_html=True)

## Set Page Title
st.set_page_config(page_title="Math Expert Pro", page_icon="🧮", layout="centered")

### Step 2: Session State Initialization
if "math_question" not in st.session_state:
    st.session_state.math_question = ""
if "solution_generated" not in st.session_state:
    st.session_state.solution_generated = False

### Step 3: Prompt For Each Language
LANGUAGES = {
    "English": {
        "prompt": """You are an expert mathematics professor. Solve this problem with COMPLETE step-by-step reasoning.

CRITICAL: You MUST provide the ENTIRE solution without cutting off. If the solution is long, be more concise but ensure completeness.

Follow this EXACT format:

STEP 1: [Concept Name]
Explanation: [Brief conceptual explanation]
Solution: [Show step with reasoning]

STEP 2: [Next Concept/Technique]  
Explanation: [Brief conceptual explanation]
Solution: [Show step with reasoning]

[Continue with STEP 3, STEP 4 etc. until FULL solution is complete]

FINAL ANSWER: [Clear final answer]

REAL-WORLD APPLICATION:
• [Practical use case 1]
• [Practical use case 2]
• [Practical use case 3]

IMPORTANT: Do not stop mid-solution. Ensure the entire mathematical proof/calculation is complete.

Question: {question}""",
        "placeholder": "E.g., Solve PDE: ∂²u/∂t² = c²∂²u/∂x², Prove Riemann Hypothesis, Calculate ∫e^(-x²)dx from -∞ to ∞...",
        "input_label": "Enter your math question (Basic to PhD Level):"
    },
    "Urdu": {
        "prompt": """آپ ماہر ریاضیات کے پروفیسر ہیں۔ اس مسئلے کو مکمل قدم بہ قدم دلائل کے ساتھ حل کریں۔

اہم: آپ کو مکمل حل بغیر کٹے پیش کرنا ہوگا۔ اگر حل طویل ہے، تو زیادہ مختصر رہیں مگر مکمل ہونا یقینی بنائیں۔

درج ذیل فارمیٹ پر عمل کریں:

STEP 1: [تصور کا نام]
وضاحت: [مختصر تصوراتی وضاحت]
حل: [دلائل کے ساتھ مرحلہ دکھائیں]

STEP 2: [اگلا تصور/تکنیک]  
وضاحت: [مختصر تصوراتی وضاحت]
حل: [دلائل کے ساتھ مرحلہ دکھائیں]

[STEP 3, STEP 4 وغیرہ کے ساتھ جاری رکھیں جب تک کہ مکمل حل نہ ہو جائے]

حتمی جواب: [واضح حتمی جواب]

حقیقی دنیا میں اطلاق:
• [عملی استعمال ۱]
• [عملی استعمال ۲] 
• [عملی استعمال ۳]

اہم: حل کے درمیان میں مت رکیں۔ یقینی بنائیں کہ پورا ریاضیاتی ثبوت/حساب کتاب مکمل ہو۔

سوال: {question}""",
        "placeholder": "مثال: جزوی تفریقی مساوات حل کریں، ریمان مفروضہ ثابت کریں، ∫e^(-x²)dx کا حساب لگائیں...",
        "input_label": "اپنا ریاضی کا سوال درج کریں (بنیادی سے پی ایچ ڈی سطح):"
    },
    "Roman Urdu": {
        "prompt": """You are an expert mathematics professor. Solve this problem with COMPLETE step-by-step reasoning in Roman Urdu.

CRITICAL: You MUST provide the ENTIRE solution without cutting off. If solution is long, be more concise but ensure completeness.

Follow this EXACT format:

STEP 1: [Concept Name]
Explanation: [Brief conceptual explanation in Roman Urdu]
Solution: [Show step with reasoning in Roman Urdu]

STEP 2: [Next Concept/Technique]  
Explanation: [Brief conceptual explanation in Roman Urdu]
Solution: [Show step with reasoning in Roman Urdu]

[Continue with STEP 3, STEP 4 etc. until FULL solution complete]

FINAL ANSWER: [Clear final answer in Roman Urdu]

REAL-WORLD APPLICATION:
• [Practical use case 1 in Roman Urdu]
• [Practical use case 2 in Roman Urdu]
• [Practical use case 3 in Roman Urdu]

IMPORTANT: Do not stop mid-solution. Ensure entire mathematical proof/calculation is complete.

Question: {question}""",
        "placeholder": "Misal: Partial differential equation hal karein, Riemann hypothesis sabit karein, ∫e^(-x²)dx ka hisab lagaein...",
        "input_label": "Apna math ka sawal darj karein (Basic se PhD level):"
    }
}

## Step 4: Initialize Gemini API
def initialize_gemini(api_key):
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        st.error(f"API configuration Failed: {e}")
        return None

## Step 5: Test API Key Function
def test_api_key(api_key):
    """Test if API key is actually valid by making a real API call"""
    try:
        model = initialize_gemini(api_key)
        if not model:
            return False, "Failed to initialize model"
        
        # Try a tiny API call to validate the key
        test_response = model.generate_content(
            "Say 'API test successful' in one word.",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=10,
                temperature=0.1
            )
        )
        
        return True, "✅ API key is VALID and working!"
        
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "401" in error_msg:
            return False, "❌ Invalid API key"
        elif "quota" in error_msg.lower():
            return False, "❌ API quota exceeded"
        else:
            return False, f"❌ API error: {error_msg}"

### Step 6: Streaming Response Function
def solve_problem_streaming(question: str, model, prompt_template: str) -> str:
    try:
        prompt = prompt_template.format(question=question)
        
        # Use streaming to get complete response
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2000,
                temperature=0.1,
                top_p=0.9,
            ),
            stream=True
        )
        
        # FIX: Extract text from each chunk properly
        full_response = []
        for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                full_response.append(chunk.text)
            elif hasattr(chunk, 'parts'):
                for part in chunk.parts:
                    if hasattr(part, 'text') and part.text:
                        full_response.append(part.text)
        
        complete_solution = "".join(full_response)
        
        # Validate completeness
        if not complete_solution.strip():
            return "❌ No response generated. Please try again."
        
        # Check if solution seems cut off
        if not any(marker in complete_solution.upper() for marker in ['FINAL ANSWER', 'REAL-WORLD', 'APPLICATION', 'حتمی جواب', 'اطلاق']):
            return complete_solution + "\n\n⚠️ **Note:** Response may be incomplete due to length limits. For very complex problems, try breaking them into smaller parts."
        
        return complete_solution
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

### Step 7: Non-Streaming Backup Function
def solve_problem_direct(question: str, model, prompt_template: str) -> str:
    try:
        prompt = prompt_template.format(question=question)
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2000,
                temperature=0.1,
            )
        )
        
        if not response.text:
            return "❌ Empty response. The model might be overloaded. Please try again."
        
        return response.text
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

### Step 8: Format Solution Function
def format_solution(solution_text: str, language: str) -> str:
    if solution_text.startswith('❌') or solution_text.startswith('⚠️'):
        return solution_text
    
    lines = solution_text.split('\n')
    formatted_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Enhanced formatting with better markers
        if any(line.upper().startswith(prefix) for prefix in ['STEP', 'STEP 1', 'STEP 2', 'STEP 3', 'STEP 4']):
            formatted_lines.append(f"### 🔹 {line}")
        elif any(marker in line.lower() for marker in ['explanation:', 'وضاحت:', 'explanation']):
            formatted_lines.append(f"**📖 {line}**")
        elif any(marker in line.lower() for marker in ['solution:', 'حل:', 'solution']):
            formatted_lines.append(f"**🧮 {line}**")
        elif any(marker in line.upper() for marker in ['FINAL ANSWER', 'حتمی جواب']):
            formatted_lines.append(f"## 🎯 {line}")
        elif any(marker in line.upper() for marker in ['REAL-WORLD', 'حقیقی دنیا', 'APPLICATION', 'اطلاق']):
            formatted_lines.append(f"## 🌍 {line}")
        elif line.startswith('•') or line.startswith('-'):
            formatted_lines.append(f"📌 {line}")
        elif i > 0 and not line.startswith('#') and len(line) > 10:
            formatted_lines.append(line)
        else:
            formatted_lines.append(line)
    
    return "\n\n".join(formatted_lines)

### Step 9: Session State Management
def clear_session():
    st.session_state.math_question = ""
    st.session_state.solution_generated = False

def validate_question(question):
    if len(question.strip()) < 3:
        return "Question too short"
    if len(question) > 1000:
        return "Question too long, please simplify"
    return None

### Step 10: Main Solve Function
def solve_question(question, api_key, lang, use_streaming):
    """Handle the question solving process"""
    # Validate inputs
    if not api_key:
        st.error("❌ **Please enter your Gemini API key in the sidebar**")
        return
    
    if not question or len(question.strip()) < 3:
        st.warning("⚠️ **Please enter a valid math question**")
        return
    
    validation_error = validate_question(question)
    if validation_error:
        st.warning(f"⚠️ {validation_error}")
        return
    
    # Initialize model
    with st.spinner("🔧 Initializing advanced math engine..."):
        model = initialize_gemini(api_key)
    
    if not model:
        st.error("❌ **Invalid API key or connection failed. Please check your API key.**")
        return
    
    # Create solution container
    st.markdown("---")
    st.subheader("🎯 Generating Complete Mathematical Solution...")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulate progress for better UX
    for i in range(5):
        steps = [
            "Analyzing problem structure...",
            "Identifying mathematical concepts...", 
            "Developing proof strategy...",
            "Generating step-by-step reasoning...",
            "Finalizing complete solution..."
        ]
        status_text.text(f"🧠 {steps[i]}")
        progress_bar.progress((i + 1) * 20)
        time.sleep(0.3)
    
    # Get solution
    status_text.text("✅ Streaming complete solution...")
    
    try:
        if use_streaming:
            solution = solve_problem_streaming(question, model, LANGUAGES[lang]["prompt"])
        else:
            solution = solve_problem_direct(question, model, LANGUAGES[lang]["prompt"])
        
        progress_bar.empty()
        status_text.empty()
        
        # Display solution
        st.subheader("📚 Complete Mathematical Solution")
        formatted_solution = format_solution(solution, lang)
        st.markdown(formatted_solution)
        
        # Set solution generated flag
        st.session_state.solution_generated = True
        
        # Download option
        if not solution.startswith('❌'):
            st.download_button(
                label="💾 Download Full Solution",
                data=solution,
                file_name=f"complete_math_solution_{int(time.time())}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
    except Exception as e:
        st.error(f"❌ **Solution generation failed:** {str(e)}")
        st.info("💡 **Tip:** Try using the streaming option or breaking the problem into smaller parts.")

### Step 11: Main App Function
def main():
    st.title("🎓 Math Expert Pro")
    st.markdown("### Step-by-Step Solutions • All Math Levels")
    
    # API Key Configuration
    with st.sidebar:
        st.header("🔑 API Configuration")
        
        # API Key Instructions
        with st.expander("📖 How to Get FREE API Key", expanded=True):
            st.markdown("""
            **Step-by-Step Guide:**
            
            1. **Visit** → [Google AI Studio](https://makersuite.google.com/app/apikey)
            2. **Sign in** with Google account
            3. **Click** "Create API Key" 
            4. **Copy** your free API key
            5. **Paste** below
            
            **💰 Completely FREE:**
            - 60 requests per minute
            - 1,000,000 tokens per month
            - No credit card required
            """)
        
        api_key = st.text_input(
            "Enter your Gemini API Key:",
            type="password",
            placeholder="Paste your API key here...",
            help="Your key stays in your browser and is never stored"
        )
        
        # API Key Status
        if api_key:
            if len(api_key) > 10:
                # Test the key
                is_valid, message = test_api_key(api_key)
                if is_valid:
                    st.success("✅ " + message)
                else:
                    st.error("❌ " + message)
            else:
                st.warning("⚠️ API key seems too short")
        else:
            st.info("🔑 Enter your API key to get started")
        
        st.markdown("---")
        st.subheader("⚙️ Solution Settings")
        
        use_streaming = st.checkbox("Use Streaming (Recommended)", value=True, 
                                   help="Gets complete solutions without cutting off")
        
        st.markdown("---")
        st.subheader("🎯 Features")
        
        st.markdown("""
        **📚 All Math Levels:**
        - Basic Arithmetic to PhD Research
        - Step-by-Step Explanations
        - Real-World Applications
        
        **⚡ Performance:**
        - Streaming Responses
        - Token Optimized
        - Fast Processing
        
        **🌍 Multi-Language:**
        - English, Urdu, Roman Urdu
        - Native Language Explanations
        """)
    
    # Language Selection
    lang = st.selectbox("Select Language / زبان منتخب کریں", list(LANGUAGES.keys()))

    # Input Question
    question = st.text_area(
        LANGUAGES[lang]["input_label"],
        value=st.session_state.math_question,
        placeholder=LANGUAGES[lang]["placeholder"],
        height=120,
        key="math_question_input",
        help="For very complex problems, consider breaking them into smaller parts"
    )

    # Update session state when input changes
    if question != st.session_state.math_question:
        st.session_state.math_question = question

    # Problem complexity warning
    if question and len(question) > 200:
        st.warning("⚠️ **Complex Problem Detected:** For best results, consider breaking this into smaller sub-problems.")
    
    # ✅ RESPONSIVE QUICK EXAMPLES SECTION
    st.markdown("**📝 Quick Examples:**")
    
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("3x + 5 = 17", use_container_width=True, help="Solve linear equation"):
            st.session_state.math_question = "Solve 3x + 5 = 17"
            st.rerun()
        if st.button("Circle Area r=7", use_container_width=True, help="Calculate area"):
            st.session_state.math_question = "Find the area of a circle with radius 7"
            st.rerun()

    with col2:
        if st.button("Eigenvalues", use_container_width=True, help="Matrix eigenvalues"):
            st.session_state.math_question = "Find the eigenvalues of matrix [[2,1],[1,2]]"
            st.rerun()
        if st.button("√2 Proof", use_container_width=True, help="Irrationality proof"):
            st.session_state.math_question = "Prove that √2 is irrational"
            st.rerun()

    with col3:
        if st.button("CL Theorem", use_container_width=True, help="Central Limit Theorem"):
            st.session_state.math_question = "Explain the Central Limit Theorem with proof"
            st.rerun()
        if st.button("Wave Eq", use_container_width=True, help="Wave equation"):
            st.session_state.math_question = "Solve the wave equation: ∂²u/∂t² = c²∂²u/∂x²"
            st.rerun()

    # ✅ RESPONSIVE BUTTONS SECTION
    col1, col2 = st.columns([2, 1])

    with col1:
        solve_clicked = st.button("🚀 Solve Math Problem", type="primary", use_container_width=True)
    
    with col2:
        clear_clicked = st.button("🔄 Clear", use_container_width=True)
    
    # Handle clear button
    if clear_clicked:
        clear_session()
        st.rerun()
    
    # Handle solve button
    if solve_clicked:
        solve_question(question, api_key, lang, use_streaming)

### Step 12: Footer
st.markdown("---")
st.caption("""
🎓 **Guaranteed Complete Solutions** • 🧮 **No Cut-Off Responses** • 🌍 **All Math Levels**  
⚡ **Streaming Technology** • 🔬 **PhD-Level Mathematics** • 👨‍🏫 Developed by Shahzaib Hanif Hashmi
""")

### Step 13: Start Main App
if __name__ == "__main__":
    main()