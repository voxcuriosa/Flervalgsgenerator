from fpdf import FPDF
import os

class QuizPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'HPT Quiz Resultat', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Side {self.page_no()}', 0, 0, 'C')

def generate_quiz_pdf(topic, user_name, score, total, percentage, questions, user_answers):
    pdf = QuizPDF()
    pdf.add_page()
    
    # Title Info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Tema: {topic}", 0, 1)
    pdf.cell(0, 10, f"Navn: {user_name}", 0, 1)
    pdf.cell(0, 10, f"Resultat: {score}/{total} ({percentage:.1f}%)", 0, 1)
    pdf.ln(10)
    
    # Questions
    for i, q in enumerate(questions):
        # Question Text
        pdf.set_font('Arial', 'B', 11)
        # Multi_cell for wrapping text
        pdf.multi_cell(0, 10, f"{i+1}. {q['question']}")
        pdf.ln(2)
        
        options = q['options']
        correct_indices = q['correct_indices']
        user_indices = user_answers.get(i, [])
        
        pdf.set_font('Arial', '', 10)
        
        for j, opt in enumerate(options):
            prefix = "[ ]"
            is_selected = j in user_indices
            is_correct = j in correct_indices
            
            # Mark selection
            if is_selected:
                prefix = "[x]"
                
            # Color logic
            # FPDF doesn't support markdown colors easily, so we use set_text_color
            if is_selected and is_correct:
                pdf.set_text_color(0, 128, 0) # Green
                status = "(Riktig)"
            elif is_selected and not is_correct:
                pdf.set_text_color(255, 0, 0) # Red
                status = "(Feil)"
            elif not is_selected and is_correct:
                pdf.set_text_color(255, 165, 0) # Orange
                status = "(Riktig svar)"
            else:
                pdf.set_text_color(0, 0, 0) # Black
                status = ""
            
            # Clean text (replace special chars if needed, FPDF is latin-1 by default)
            # We need to handle unicode. FPDF 1.7.2 has issues with utf-8.
            # We might need to replace characters or use a font that supports it.
            # For simplicity, let's try to encode/decode or replace.
            # Or use a compatible font. Arial is standard but might miss some chars.
            # Let's try to handle basic Norwegian chars.
            
            opt_text = f"{prefix} {opt} {status}"
            try:
                opt_text = opt_text.encode('latin-1', 'replace').decode('latin-1')
            except:
                opt_text = opt_text.encode('ascii', 'replace').decode('ascii')
                
            pdf.cell(0, 8, opt_text, 0, 1)
            
        pdf.set_text_color(0, 0, 0) # Reset
        
        # Justification
        if 'justification' in q:
            pdf.ln(2)
            pdf.set_font('Arial', 'I', 9)
            just = f"Begrunnelse: {q['justification']}"
            try:
                just = just.encode('latin-1', 'replace').decode('latin-1')
            except:
                just = just.encode('ascii', 'replace').decode('ascii')
            pdf.multi_cell(0, 6, just)
            
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    # Output
    # We return the bytes
    return pdf.output(dest='S').encode('latin-1')
