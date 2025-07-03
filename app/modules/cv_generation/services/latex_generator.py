import os
import subprocess
import tempfile
import shutil
from typing import Optional, Dict, Any
from pathlib import Path
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LaTeXGeneratorService:
    """Service xử lý compile LaTeX thành PDF"""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = "temp_cvs"  # Directory lưu output files

        # Tạo output directory nếu chưa có
        os.makedirs(self.output_dir, exist_ok=True)

        # ============ DEBUG MODE - REMOVE IN PRODUCTION ============
        # DEBUG: Create debug directory for LaTeX source storage
        self.debug_mode = os.environ.get("CV_DEBUG_MODE", "false").lower() == "true"
        if self.debug_mode:
            self.debug_dir = "debug_latex"
            os.makedirs(self.debug_dir, exist_ok=True)
            logger.info(
                f"🐛 DEBUG MODE ENABLED: LaTeX sources will be saved to {self.debug_dir}"
            )
        # ============ END DEBUG MODE ============

    async def compile_latex_to_pdf(
        self, latex_source: str, filename: Optional[str] = None, cleanup: bool = True
    ) -> Dict[str, Any]:
        """
        Compile LaTeX source thành PDF

        Args:
            latex_source: Source LaTeX code
            filename: Tên file output (optional)
            cleanup: Có cleanup temp files không

        Returns:
            Dict chứa thông tin file PDF
        """
        try:
            # Tạo unique filename nếu không có
            if not filename:
                filename = f"cv_{uuid.uuid4().hex[:8]}"

            # Tạo paths
            tex_filename = f"{filename}.tex"
            pdf_filename = f"{filename}.pdf"

            # Tạo temp directory cho compilation
            compile_dir = os.path.join(self.temp_dir, f"compile_{uuid.uuid4().hex[:8]}")
            os.makedirs(compile_dir, exist_ok=True)

            tex_path = os.path.join(compile_dir, tex_filename)
            pdf_path = os.path.join(compile_dir, pdf_filename)

            # ============ DEBUG MODE - REMOVE IN PRODUCTION ============
            # DEBUG: Save LaTeX source to debug folder for inspection
            if self.debug_mode:
                debug_filename = f"debug_{filename}_{uuid.uuid4().hex[:4]}.tex"
                debug_path = os.path.join(self.debug_dir, debug_filename)
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(latex_source)
                logger.info(f"🐛 DEBUG: LaTeX source saved to {debug_path}")
            # ============ END DEBUG MODE ============

            # Fix LaTeX compatibility issues
            latex_source_fixed = self._fix_latex_compatibility(latex_source)

            # ============ DEBUG MODE - REMOVE IN PRODUCTION ============
            # DEBUG: Save fixed LaTeX source for comparison
            if self.debug_mode:
                debug_fixed_filename = (
                    f"debug_{filename}_FIXED_{uuid.uuid4().hex[:4]}.tex"
                )
                debug_fixed_path = os.path.join(self.debug_dir, debug_fixed_filename)
                with open(debug_fixed_path, "w", encoding="utf-8") as f:
                    f.write(latex_source_fixed)
                logger.info(f"🐛 DEBUG: Fixed LaTeX source saved to {debug_fixed_path}")
            # ============ END DEBUG MODE ============

            # Ghi LaTeX source vào file với safe encoding
            try:
                with open(tex_path, "w", encoding="utf-8") as f:
                    f.write(latex_source_fixed)
                logger.info(f"✅ LaTeX source written to: {tex_path}")
            except UnicodeEncodeError as e:
                logger.error(f"❌ Unicode encoding error when writing LaTeX file: {e}")
                # Try to clean the source more aggressively
                cleaned_source = latex_source_fixed.encode(
                    "utf-8", errors="ignore"
                ).decode("utf-8")
                with open(tex_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_source)
                logger.warning("⚠️ Used aggressive character cleaning for file write")
            except Exception as e:
                logger.error(f"❌ Error writing LaTeX file: {e}")
                raise

            # Compile LaTeX
            compilation_result = await self._compile_latex(compile_dir, tex_filename)

            if not compilation_result["success"]:
                raise Exception(
                    f'LaTeX compilation failed: {compilation_result["error"]}'
                )

            # Copy PDF to output directory
            output_pdf_path = os.path.join(self.output_dir, pdf_filename)
            shutil.copy2(pdf_path, output_pdf_path)

            # Get file info
            file_size = os.path.getsize(output_pdf_path)

            # Cleanup temp directory nếu requested
            if cleanup:
                shutil.rmtree(compile_dir, ignore_errors=True)

            return {
                "success": True,
                "pdf_path": output_pdf_path,
                "pdf_filename": pdf_filename,
                "file_size": file_size,
                "latex_source": latex_source,
                "compilation_log": compilation_result.get("log", ""),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "pdf_path": None, "file_size": 0}

    def _fix_latex_compatibility(self, latex_source: str) -> str:
        """
        Fix LaTeX compatibility issues for pdflatex

        ============ DEBUG MODE - REMOVE IN PRODUCTION ============
        This method fixes common compatibility issues between AI-generated
        LaTeX and pdflatex compiler.
        ============ END DEBUG MODE ============
        """
        try:
            logger.info("🔧 Fixing LaTeX compatibility issues...")

            # Fix 0: Handle encoding issues first
            latex_source = self._fix_encoding_issues(latex_source)

            # Fix 1: Remove fontspec package (XeLaTeX/LuaLaTeX only)
            if "\\usepackage{fontspec}" in latex_source:
                logger.warning(
                    "⚠️ Removing fontspec package (incompatible with pdflatex)"
                )
                latex_source = latex_source.replace("\\usepackage{fontspec}", "")

            # Fix 2: Remove fontspec with options
            import re

            latex_source = re.sub(r"\\usepackage\[.*?\]\{fontspec\}", "", latex_source)

            # Fix 2.1: Remove other XeLaTeX/LuaLaTeX specific packages
            incompatible_packages = [
                "fontenc-xunicode",
                "xltxtra",
                "xunicode",
                "polyglossia",
                "fontawesome",
                "fontawesome5",
            ]
            for pkg in incompatible_packages:
                pattern = rf"\\usepackage(?:\[.*?\])?\{{{pkg}\}}"
                if re.search(pattern, latex_source):
                    logger.warning(f"⚠️ Removing incompatible package: {pkg}")
                    latex_source = re.sub(
                        pattern,
                        f"% Package {pkg} removed for pdflatex compatibility",
                        latex_source,
                    )

            # Fix 3: Replace Unicode-specific commands with pdflatex-compatible ones
            unicode_fixes = {
                "\\setmainfont": "% \\setmainfont (removed for pdflatex compatibility)",
                "\\setsansfont": "% \\setsansfont (removed for pdflatex compatibility)",
                "\\setmonofont": "% \\setmonofont (removed for pdflatex compatibility)",
                "\\defaultfontfeatures": "% \\defaultfontfeatures (removed for pdflatex compatibility)",
                "\\newfontfamily": "% \\newfontfamily (removed for pdflatex compatibility)",
                "\\addfontfeatures": "% \\addfontfeatures (removed for pdflatex compatibility)",
                "\\newfontface": "% \\newfontface (removed for pdflatex compatibility)",
            }

            for old_cmd, replacement in unicode_fixes.items():
                # Handle commands with parameters
                pattern = rf"{re.escape(old_cmd)}(?:\[.*?\])?(?:\{{.*?\}})*"
                if re.search(pattern, latex_source):
                    logger.warning(f"⚠️ Replacing {old_cmd} for pdflatex compatibility")
                    latex_source = re.sub(pattern, replacement, latex_source)

            # Fix 4: Ensure proper font encoding
            if (
                "\\usepackage[utf8]{inputenc}" not in latex_source
                and "\\usepackage{inputenc}" not in latex_source
            ):
                # Add input encoding after documentclass
                latex_source = re.sub(
                    r"(\\documentclass.*?\n)",
                    r"\1\\usepackage[utf8]{inputenc}\n\\usepackage[T1]{fontenc}\n",
                    latex_source,
                    count=1,
                )
                logger.info("✅ Added UTF-8 input encoding for pdflatex")

            # Fix 5: Final validation check
            remaining_fontspec = re.search(
                r"\\(?:setmainfont|setsansfont|setmonofont|fontspec)", latex_source
            )
            if remaining_fontspec:
                logger.error(
                    f"❌ Still found fontspec commands after fixes: {remaining_fontspec.group()}"
                )
                # Force remove any remaining fontspec references
                latex_source = re.sub(
                    r"\\(?:setmainfont|setsansfont|setmonofont).*?(?=\\|\n|$)",
                    "% Font command removed for pdflatex compatibility",
                    latex_source,
                )
                logger.warning("⚠️ Force removed remaining font commands")

            logger.info("✅ LaTeX compatibility fixes applied")
            return latex_source

        except Exception as e:
            logger.error(f"❌ Error fixing LaTeX compatibility: {e}")
            return latex_source  # Return original if fixes fail

    def _fix_encoding_issues(self, latex_source: str) -> str:
        """
        Fix encoding issues in LaTeX source

        ============ DEBUG MODE - REMOVE IN PRODUCTION ============
        This method handles problematic characters that cause UTF-8 decoding errors
        ============ END DEBUG MODE ============
        """
        try:
            logger.info("🔤 Fixing encoding issues...")

            # If input is bytes, decode it properly
            if isinstance(latex_source, bytes):
                try:
                    latex_source = latex_source.decode("utf-8")
                except UnicodeDecodeError:
                    # Try other encodings
                    for encoding in ["latin1", "cp1252", "iso-8859-1"]:
                        try:
                            latex_source = latex_source.decode(encoding)
                            logger.warning(f"⚠️ Decoded using {encoding} encoding")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Fallback: decode with errors='replace'
                        latex_source = latex_source.decode("utf-8", errors="replace")
                        logger.warning("⚠️ Decoded with error replacement")

            # Handle problematic Unicode characters
            unicode_replacements = {
                # Smart quotes
                """: "``",        # Left double quotation mark
                """: "''",  # Right double quotation mark
                "'": "`",  # Left single quotation mark
                "'": "'",  # Right single quotation mark
                # Dashes
                "–": "--",  # En dash
                "—": "---",  # Em dash
                # Other common problematic characters
                "…": "\\ldots{}",  # Horizontal ellipsis
                "•": "\\textbullet{}",  # Bullet
                "©": "\\copyright{}",  # Copyright
                "®": "\\textregistered{}",  # Registered trademark
                "™": "\\texttrademark{}",  # Trademark
                # Accented characters (common ones)
                "á": "\\'{a}",
                "à": "\\`{a}",
                "ä": '\\""{a}',
                "â": "\\^{a}",
                "ã": "\\~{a}",
                "é": "\\'{e}",
                "è": "\\`{e}",
                "ë": '\\""{e}',
                "ê": "\\^{e}",
                "í": "\\'{i}",
                "ì": "\\`{i}",
                "ï": '\\""{i}',
                "î": "\\^{i}",
                "ó": "\\'{o}",
                "ò": "\\`{o}",
                "ö": '\\""{o}',
                "ô": "\\^{o}",
                "õ": "\\~{o}",
                "ú": "\\'{u}",
                "ù": "\\`{u}",
                "ü": '\\""{u}',
                "û": "\\^{u}",
                "ç": "\\c{c}",
                "ñ": "\\~{n}",
            }

            replacement_count = 0
            for unicode_char, latex_cmd in unicode_replacements.items():
                if unicode_char in latex_source:
                    count = latex_source.count(unicode_char)
                    latex_source = latex_source.replace(unicode_char, latex_cmd)
                    replacement_count += count
                    logger.info(
                        f"✅ Replaced {count}x '{unicode_char}' with '{latex_cmd}'"
                    )

            if replacement_count > 0:
                logger.info(f"✅ Fixed {replacement_count} encoding issues")
            else:
                logger.info("✅ No encoding issues found")

            # Ensure the result is clean UTF-8
            try:
                latex_source.encode("utf-8")
            except UnicodeEncodeError as e:
                logger.error(f"❌ Still has encoding issues after fixes: {e}")
                # Remove problematic characters as last resort
                latex_source = latex_source.encode("utf-8", errors="ignore").decode(
                    "utf-8"
                )
                logger.warning("⚠️ Removed problematic characters as fallback")

            return latex_source

        except Exception as e:
            logger.error(f"❌ Error fixing encoding: {e}")
            # Fallback: try to clean the string
            try:
                if isinstance(latex_source, bytes):
                    latex_source = latex_source.decode("utf-8", errors="replace")
                return latex_source.encode("utf-8", errors="ignore").decode("utf-8")
            except:
                return str(latex_source)  # Last resort

    async def _compile_latex(
        self, compile_dir: str, tex_filename: str
    ) -> Dict[str, Any]:
        """Compile LaTeX file"""
        logger.info(f"🔧 Starting LaTeX compilation for: {tex_filename}")
        logger.info(f"📁 Compile directory: {compile_dir}")

        try:
            # Check if pdflatex exists first
            logger.info("🔍 Checking pdflatex availability...")
            try:
                version_check = subprocess.run(
                    ["pdflatex", "--version"], capture_output=True, text=True, timeout=5
                )
                if version_check.returncode == 0:
                    logger.info(
                        f"✅ pdflatex found: {version_check.stdout.split(chr(10))[0]}"
                    )
                else:
                    logger.error(
                        f"❌ pdflatex version check failed: {version_check.stderr}"
                    )
            except FileNotFoundError:
                logger.error("❌ pdflatex command not found in PATH")
                logger.info("🔍 Available commands in PATH:")
                try:
                    path_result = subprocess.run(
                        ["which", "pdflatex"], capture_output=True, text=True
                    )
                    logger.info(f'which pdflatex: {path_result.stdout or "Not found"}')

                    # Check TeX Live installation
                    tex_check = subprocess.run(
                        ["which", "tex"], capture_output=True, text=True
                    )
                    logger.info(f'which tex: {tex_check.stdout or "Not found"}')

                    # List installed packages
                    dpkg_check = subprocess.run(
                        ["dpkg", "-l", "*tex*"], capture_output=True, text=True
                    )
                    logger.info(f"TeX packages installed: {dpkg_check.stdout[:500]}...")
                except Exception as e:
                    logger.error(f"Could not check system commands: {e}")

                return {
                    "success": False,
                    "error": "pdflatex not found. Please install LaTeX distribution.",
                }
            except Exception as e:
                logger.error(f"❌ Error checking pdflatex: {e}")

            # Chạy pdflatex
            cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory",
                compile_dir,
                tex_filename,
            ]

            logger.info(f'🚀 Running command: {" ".join(cmd)}')

            # Chạy 2 lần để ensure references được resolve
            for i in range(2):
                logger.info(f"📋 LaTeX compilation pass {i + 1}/2")

                process = subprocess.run(
                    cmd, cwd=compile_dir, capture_output=True, text=True, timeout=30
                )

                logger.info(f"📊 Return code: {process.returncode}")
                logger.info(f"📝 STDOUT (first 1000 chars): {process.stdout[:1000]}")
                if process.stderr:
                    logger.warning(f"⚠️ STDERR: {process.stderr}")

                if process.returncode != 0:
                    logger.error(f"❌ pdflatex failed on pass {i + 1}")

                    # ============ DEBUG MODE - REMOVE IN PRODUCTION ============
                    # DEBUG: Save compilation logs on failure
                    if hasattr(self, "debug_mode") and self.debug_mode:
                        log_filename = f"compile_error_{uuid.uuid4().hex[:8]}.log"
                        log_path = os.path.join(self.debug_dir, log_filename)
                        with open(log_path, "w", encoding="utf-8") as f:
                            f.write(f"=== COMPILATION ERROR LOG ===\n")
                            f.write(f"Return code: {process.returncode}\n")
                            f.write(f"STDERR:\n{process.stderr}\n\n")
                            f.write(f"STDOUT:\n{process.stdout}\n")
                        logger.info(
                            f"🐛 DEBUG: Compilation error log saved to {log_path}"
                        )
                    # ============ END DEBUG MODE ============

                    return {
                        "success": False,
                        "error": f"pdflatex failed: {process.stderr}",
                        "log": process.stdout,
                    }
                else:
                    logger.info(f"✅ Pass {i + 1} completed successfully")

            logger.info("🎉 LaTeX compilation completed successfully!")
            return {"success": True, "log": process.stdout}

        except subprocess.TimeoutExpired:
            logger.error("⏰ LaTeX compilation timeout (30s)")
            return {"success": False, "error": "LaTeX compilation timeout"}
        except FileNotFoundError as e:
            logger.error(f"❌ FileNotFoundError: {e}")
            return {
                "success": False,
                "error": "pdflatex not found. Please install LaTeX distribution.",
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error during LaTeX compilation: {e}")
            return {"success": False, "error": str(e)}

    def validate_latex_source(self, latex_source: str) -> Dict[str, Any]:
        """Validate LaTeX source code"""
        try:
            # Basic validation
            if not latex_source.strip():
                return {"valid": False, "error": "Empty LaTeX source"}

            # Check for required elements
            required_elements = [
                "\\documentclass",
                "\\begin{document}",
                "\\end{document}",
            ]

            for element in required_elements:
                if element not in latex_source:
                    return {
                        "valid": False,
                        "error": f"Missing required element: {element}",
                    }

            # Check for balanced braces (basic check)
            open_braces = latex_source.count("{")
            close_braces = latex_source.count("}")

            if open_braces != close_braces:
                return {
                    "valid": False,
                    "error": f"Unbalanced braces: {open_braces} open, {close_braces} close",
                }

            return {"valid": True, "message": "LaTeX source is valid"}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def get_latex_packages_info(self) -> Dict[str, Any]:
        """Get thông tin về LaTeX packages có sẵn"""
        logger.info("🔍 Checking LaTeX system information...")

        try:
            # Check if pdflatex is available
            logger.info("🧪 Testing pdflatex command...")
            result = subprocess.run(
                ["pdflatex", "--version"], capture_output=True, text=True, timeout=5
            )

            logger.info(f"📊 pdflatex version check return code: {result.returncode}")
            if result.stdout:
                logger.info(f"📝 pdflatex version output: {result.stdout[:200]}...")
            if result.stderr:
                logger.warning(f"⚠️ pdflatex version stderr: {result.stderr}")

            if result.returncode == 0:
                # Additional system checks
                system_info = {
                    "latex_available": True,
                    "version_info": result.stdout.split("\n")[0],
                    "supported_packages": [
                        "geometry",
                        "xcolor",
                        "fontspec",
                        "enumitem",
                        "titlesec",
                        "tikz",
                        "graphicx",
                        "hyperref",
                        "fontawesome",
                        "academicons",
                    ],
                }

                # Check additional LaTeX tools
                try:
                    logger.info("🔧 Checking additional LaTeX tools...")

                    # Check for latex command
                    latex_check = subprocess.run(
                        ["latex", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    system_info["latex_command_available"] = latex_check.returncode == 0

                    # Check for kpsewhich (package finder)
                    kpse_check = subprocess.run(
                        ["kpsewhich", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    system_info["kpsewhich_available"] = kpse_check.returncode == 0

                    # Check environment variables
                    system_info["path_env"] = os.environ.get("PATH", "")[:200] + "..."
                    system_info["texmfhome"] = os.environ.get("TEXMFHOME", "Not set")

                    logger.info(f"✅ LaTeX system check completed: {system_info}")

                except Exception as tool_check_error:
                    logger.warning(
                        f"⚠️ Error checking additional tools: {tool_check_error}"
                    )
                    system_info["additional_tools_error"] = str(tool_check_error)

                return system_info
            else:
                logger.error("❌ pdflatex not available")
                return {"latex_available": False, "error": "pdflatex not found"}

        except FileNotFoundError as e:
            logger.error(f"❌ pdflatex command not found: {e}")

            # Try to provide helpful debugging info
            try:
                logger.info("🔍 Attempting to find LaTeX installation...")

                # Check common LaTeX installation paths
                common_paths = [
                    "/usr/bin/pdflatex",
                    "/usr/local/bin/pdflatex",
                    "/opt/texlive/*/bin/*/pdflatex",
                ]

                for path in common_paths:
                    if os.path.exists(path):
                        logger.info(f"📍 Found pdflatex at: {path}")
                        break
                else:
                    logger.warning("❌ No pdflatex found in common paths")

                # Check if any TeX packages are installed
                try:
                    dpkg_result = subprocess.run(
                        ["dpkg", "-l", "*tex*"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if dpkg_result.returncode == 0:
                        logger.info(
                            f"📦 TeX packages found: {dpkg_result.stdout[:300]}..."
                        )
                    else:
                        logger.info("📦 No TeX packages found via dpkg")
                except:
                    logger.info("📦 Could not check TeX packages via dpkg")

            except Exception as debug_error:
                logger.warning(f"⚠️ Error during debug checks: {debug_error}")

            return {"latex_available": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Unexpected error checking LaTeX: {e}")
            return {"latex_available": False, "error": str(e)}

    def cleanup_temp_files(self):
        """Cleanup temporary files"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)

            # Recreate temp directory
            self.temp_dir = tempfile.mkdtemp()

        except Exception as e:
            print(f"Error during cleanup: {e}")

    def __del__(self):
        """Cleanup khi object bị destroy"""
        self.cleanup_temp_files()
