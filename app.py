import streamlit as st
import requests

# Streamlit UI setup
st.set_page_config(page_title="📄 Sumry", layout="wide")


# Header
st.title("📄 Sumry: AI-Powered Arxiv Paper Summarizer Tool")
st.markdown("Extract and summarize research papers with AI-powered efficiency.")

# Input
pdf_url = st.text_input("🔗 Enter the Arxiv PDF URL:",
                        placeholder="Paste arxiv paper url here..")

status_placeholder = st.empty()

def format_section(title, content):
    """Format each summary section."""
    return f"""
    <div class="summary-section">
        <div class="section-title">{title}</div>
        <div class="section-content">{content}</div>
    </div>
    """

# Submit button
if st.button("🚀 Summarize PDF"):
    if pdf_url:
        with st.spinner("⏳ Processing... This may take a few minutes."):
            status_placeholder.info("Fetching and summarizing the document...")
            try:
                response = requests.post(
                    "http://localhost:8000/summarize_arxiv/",
                    json={"url": pdf_url},
                    timeout=3600
                )
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        status_placeholder.error(f"❌ {data['error']}")
                    else:
                        summary = data.get("summary", "No summary generated.")
                        status_placeholder.success("✅ Summary Ready!")

                        # Display formatted sections
                        sections = summary.split("#")[1:]  # skip empty before first #

                        for section in sections:
                            if section.strip():
                                parts = section.split("\n", 1)
                                if len(parts) == 2:
                                    title, content = parts
                                    st.markdown(format_section(title.strip(), content.strip()), unsafe_allow_html=True)

                        st.download_button("⬇️ Download Summary", summary, file_name="paper_summary.md", mime="text/markdown")
                else:
                    status_placeholder.error("❌ Failed to process the PDF. Check the URL and try again.")
            except requests.exceptions.Timeout:
                status_placeholder.error("⚠️ Request timed out. Please try again later.")
            except Exception as e:
                status_placeholder.error(f"⚠️ Error: {str(e)}")
    else:
        status_placeholder.warning("⚠️ Please enter a valid Arxiv PDF URL.")


