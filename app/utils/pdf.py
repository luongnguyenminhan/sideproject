import os
import fitz


class MDToPDFConverter:
	def __init__(self, markdown_text: str, css_path: str | None = None):
		self.markdown_text = markdown_text
		self.css_path = css_path

		# Default CSS if no custom CSS is provided
		self.default_css = """
        /* Import fonts at the beginning to avoid warnings */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Open+Sans:wght@400;600&display=swap');
        
        @page {
          size: A4;
          margin: 2.5cm 2cm;
          @top-center {
            content: "cgsem.ai";
            font-family: 'Montserrat', sans-serif;
            font-size: 10pt;
            font-weight: 600;
            color: #000000;
            border-bottom: 1px solid #f37021;
            padding-bottom: 0.5cm;
          }
          @bottom-center {
            content: "Trang " counter(page) " / " counter(pages);
            font-family: 'Montserrat', sans-serif;
            font-size: 8pt;
            color: #4d4d4d;
            border-top: 1px solid #f37021;
            padding-top: 0.5cm;
          }
        }

        :root {
          --primary-color: #f37021;
          --secondary-color: #ff8a45;
          --text-color: #000000;
          --light-text: #4d4d4d;
          --border-color: #e0e0e0;
          --bg-light: #ffffff;
          --bg-highlight: #fff2eb;
          --accent-color: #f37021;
        }

        body {
          font-family: 'Open Sans', sans-serif;
          line-height: 1.6;
          color: var(--text-color);
          font-size: 9pt;
          max-width: 100%;
          margin: 0;
          padding: 0;
          background-color: var(--bg-light);
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
          font-family: 'Montserrat', sans-serif;
          margin-top: 1.8em;
          margin-bottom: 0.7em;
          line-height: 1.3;
          color: var(--primary-color);
        }

        h1 {
          font-size: 16pt;
          font-weight: 700;
          text-align: center;
          margin-top: 1em;
          padding-bottom: 0.5em;
          border-bottom: 2px solid var(--accent-color);
        }

        h2 {
          font-size: 13pt;
          font-weight: 600;
          padding-bottom: 0.3em;
          border-bottom: 1px solid var(--accent-color);
        }

        h3 {
          font-size: 11pt;
          font-weight: 600;
        }

        h4 {
          font-size: 10pt;
          font-weight: 600;
        }

        /* Paragraphs and text */
        p {
          margin-bottom: 1em;
          text-align: justify;
        }

        /* Lists */
        ul, ol {
          padding-left: 1.6em;
          margin-bottom: 1.3em;
        }

        li {
          margin-bottom: 0.4em;
        }

        li > ul, li > ol {
          margin-top: 0.4em;
          margin-bottom: 0.4em;
        }

        /* Code blocks */
        code {
          font-family: 'Fira Code', monospace;
          background-color: #fff2eb;
          padding: 0.2em 0.4em;
          border-radius: 3px;
          font-size: 0.9em;
          color: var(--primary-color);
        }

        pre {
          background-color: #fff2eb;
          padding: 1em;
          border-radius: 5px;
          /* Fix for overflow-x property */
          overflow: auto;
          border-left: 3px solid var(--accent-color);
          margin: 1.3em 0;
        }

        pre code {
          background-color: transparent;
          padding: 0;
          font-size: 8pt;
          color: var(--text-color);
        }

        /* Rest of CSS as provided */
        """

	def convert(self) -> bytes:
		"""
		Convert the markdown text to a styled PDF file using WeasyPrint.
		"""
		import io

		import markdown2
		from weasyprint import CSS, HTML

		# Convert markdown to HTML with extra features
		html_content = markdown2.markdown(self.markdown_text, extras=['tables', 'fenced-code-blocks', 'code-friendly'])

		# Use custom CSS if provided, otherwise use default
		css_content = self.default_css
		if self.css_path and os.path.exists(self.css_path):
			with open(self.css_path) as f:
				css_content = f.read()

		# Create CSS object to properly handle CSS rules
		css = CSS(string=css_content)

		# Create HTML document
		html = HTML(string=f'<html><head></head><body>{html_content}</body></html>')

		# Generate PDF into a bytes buffer
		pdf_buffer = io.BytesIO()
		html.write_pdf(pdf_buffer, stylesheets=[css])

		# Return the PDF as bytes
		pdf_buffer.seek(0)
		return pdf_buffer.read()


class PDFToTextConverter:
	def __init__(self, file_path: str):
		self.file_path = file_path
		self.doc = fitz.open(file_path)

	def extract_text(self) -> dict:
		"""
		Extracts text from the PDF in multiple formats and returns a dictionary
		with format types as keys and their corresponding content as values.

		Returns:
		    dict: A dictionary containing the extracted text in different formats.
		"""
		try:
			print('[DEBUG] Starting PDF text extraction in multiple formats')
			print(f'[DEBUG] Processing PDF file: {self.file_path}')
			print(f'[DEBUG] Document has {len(self.doc)} pages')

			result = {}

			# Extract content in each format
			result['text'] = '\n'.join([page.get_text('text') for page in self.doc])
			return result
		except Exception as e:
			print(f'[DEBUG] Error extracting text from PDF: {str(e)}')
			print(f'[DEBUG] Exception type: {type(e).__name__}')
			print(f'[DEBUG] Exception occurred in file: {self.file_path}')
			return {}  # Return empty dict or raise a custom exception

	@staticmethod
	def extract_text_from_file(file_content, filetype='pdf'):
		"""
		Extracts text from a PDF file content in multiple formats.

		Args:
		    file_content: File content as BytesIO or bytes
		    filetype: Type of file (default: 'pdf')

		Returns:
		    dict: Dictionary with extracted text
		"""
		results = {}
		try:
			# Handle different input types
			if hasattr(file_content, 'read'):
				# It's already a file-like object
				doc = fitz.open(stream=file_content, filetype=filetype)
			else:
				# It's bytes, convert to BytesIO
				import io

				file_stream = io.BytesIO(file_content)
				doc = fitz.open(stream=file_stream, filetype=filetype)

			# Extract text from all pages
			text_parts = []
			for page in doc:
				page_text = page.get_text('text')
				if page_text.strip():
					text_parts.append(page_text)

			results['text'] = '\n'.join(text_parts)
			doc.close()

			return results
		except Exception as e:
			print(f'[DEBUG] Error extracting text from PDF: {str(e)}')
			return {'text': ''}  # Return empty text instead of empty dict

	def search_for_text(self, search_string: str) -> list:
		"""
		Searches for a string in the PDF and returns a list of rectangles for each occurrence.
		"""
		results = []
		for page in self.doc:
			results.extend(page.search_for(search_string))
		return results

	def close(self):
		self.doc.close()
