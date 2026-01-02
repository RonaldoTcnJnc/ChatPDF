import os
import threading
from pathlib import Path
from typing import Optional, List, Tuple

import flet as ft
from chatbot_rag import ChatbotRAG

class ChatbotGUI:
    def __init__(self):
        """Inicializa la interfaz gráfica del Chatbot."""
        self.chatbot = ChatbotRAG()
        self.chat_messages: List[Tuple[str, str]] = []
        self.processing: bool = False
        self.current_pdf: Optional[str] = None  # Rastrear el PDF seleccionado actualmente
        self.available_pdfs: List[str] = []  # Lista de PDFs disponibles

    def main(self, page: ft.Page):
        page.title = "🤖 Chatbot RAG Local"
        page.window.width = 900
        page.window.height = 700
        page.theme_mode = ft.ThemeMode.DARK

        # Color scheme
        primary_color = "#1E88E5"
        secondary_color = "#424242"
        bg_color = "#121212"

        page.bgcolor = bg_color

        # Header
        header = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "🤖 Chatbot RAG Local",
                        size=28,
                        weight="bold",
                        color="white"
                    ),
                    ft.Text(
                        "Powered by Llama 3 & ChromaDB",
                        size=12,
                        color="#B0BEC5"
                    ),
                ],
                spacing=5
            ),
            padding=20,
            bgcolor=secondary_color,
            border_radius=10
        )

        # Chat display area
        self.chat_display = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
            auto_scroll=True
        )

        # Stats area
        self.stats_text = ft.Text(
            "📊 Estado: Inicializando...",
            size=10,
            color="#B0BEC5"
        )

        # PDF selector dropdown
        self.pdf_dropdown = ft.Dropdown(
            label="📄 Selecciona un PDF",
            width=250,
            filled=True,
            bgcolor="#1E1E1E",
            border_color=primary_color,
            label_style=ft.TextStyle(color="#B0BEC5"),
            text_style=ft.TextStyle(color="white"),
            on_change=self.on_pdf_selected
        )

        # Input area
        self.input_field = ft.TextField(
            label="Escribe tu pregunta...",
            multiline=True,
            min_lines=1,
            max_lines=3,
            filled=True,
            bgcolor="#1E1E1E",
            border_color=primary_color,
            label_style=ft.TextStyle(color="#B0BEC5"),
            text_style=ft.TextStyle(color="white"),
            expand=True
        )

        send_btn = ft.ElevatedButton(
            "📤 Enviar",
            bgcolor=primary_color,
            color="white",
            on_click=self.send_message
        )

        input_row = ft.Row(
            [self.pdf_dropdown, self.input_field, send_btn],
            spacing=10,
            expand=True
        )

        # Control buttons
        load_pdf_btn = ft.ElevatedButton(
            "📁 Cargar PDFs",
            on_click=self.load_pdf_dialog
        )

        clear_btn = ft.ElevatedButton(
            "🗑️ Limpiar Chat",
            on_click=self.clear_chat
        )

        clear_db_btn = ft.ElevatedButton(
            "🧹 Limpiar BD",
            on_click=self.clear_database
        )

        stats_btn = ft.ElevatedButton(
            "📊 Estadísticas",
            on_click=self.show_stats
        )

        control_row = ft.Row(
            [load_pdf_btn, clear_btn, clear_db_btn, stats_btn],
            spacing=10,
            wrap=True
        )

        # Main container
        main_content = ft.Column(
            [
                header,
                ft.Divider(height=1, color="#333333"),
                self.chat_display,
                self.stats_text,
                input_row,
                control_row
            ],
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )

        # File picker for PDF loading
        self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result)
        page.overlay.append(self.file_picker)

        page.add(
            ft.Container(
                content=main_content,
                expand=True,
                padding=15
            )
        )

        # Initialize stats
        self.update_stats()

    def send_message(self, e: ft.ControlEvent):
        message = self.input_field.value.strip()
        if not message or self.processing:
            return

        if not self.current_pdf:
            self.add_message_to_display("⚠️ Sistema", "Por favor, selecciona un PDF primero", is_user=False)
            return

        self.input_field.value = ""
        self.input_field.update()

        # Add user message to display
        self.add_message_to_display("Tú", message, is_user=True)

        # Process in background
        self.processing = True
        thread = threading.Thread(target=self.process_message, args=(message,))
        thread.daemon = True
        thread.start()

    def process_message(self, message: str):
        try:
            # Llamar al modelo con RAG usando el PDF seleccionado
            # k=5 fragmentos recuperados (balance entre contexto y tokens)
            response = self.chatbot.get_response(message, use_rag=True, k=5, pdf_name=self.current_pdf)
            self.add_message_to_display("🤖 Modelo", response, is_user=False)
            self.chat_messages.append(("bot", response))
        except Exception as e:
            self.add_message_to_display("❌ Error", f"Error: {str(e)}", is_user=False)
        finally:
            self.processing = False

    def add_message_to_display(self, sender: str, message: str, is_user: bool = False):
        # Color based on sender
        if is_user:
            bg_color = "#1E88E5"
            text_color = "white"
            alignment = ft.MainAxisAlignment.END
        else:
            bg_color = "#424242"
            text_color = "#E3F2FD"
            alignment = ft.MainAxisAlignment.START

        # Create message container
        msg_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text(sender, size=10, weight="bold", color="#90CAF9"),
                    ft.Text(message, size=12, color=text_color, selectable=True)
                ],
                spacing=5
            ),
            padding=12,
            bgcolor=bg_color,
            border_radius=10,
            width=600
        )

        msg_row = ft.Row(
            [msg_container],
            alignment=alignment
        )

        self.chat_display.controls.append(msg_row)
        self.chat_display.update()

    def load_pdf_dialog(self, e):
        self.file_picker.pick_files(
            allowed_extensions=["pdf"],
            dialog_title="Selecciona PDFs para cargar"
        )

    def on_file_picker_result(self, e):
        if e.files:
            self.add_message_to_display("📂 Sistema", f"Cargando {len(e.files)} archivo(s)...", is_user=False)

            for file in e.files:
                try:
                    self.chatbot.load_single_pdf(file.path)
                    pdf_name = Path(file.path).name
                    self.add_message_to_display(
                        "✅ Sistema",
                        f"✓ PDF cargado: {pdf_name}\n📚 Se guardó en su propio espacio en la BD",
                        is_user=False
                    )
                except Exception as ex:
                    self.add_message_to_display(
                        "❌ Error",
                        f"Error cargando {Path(file.path).name}: {str(ex)}",
                        is_user=False
                    )

            self.update_stats()
            self.refresh_pdf_list()

    def on_pdf_selected(self, e):
        """Se ejecuta cuando el usuario selecciona un PDF del dropdown"""
        if self.pdf_dropdown.value:
            self.current_pdf = self.pdf_dropdown.value
            self.add_message_to_display(
                "📄 PDF Seleccionado",
                f"Ahora consultas sobre: {self.current_pdf}",
                is_user=False
            )



    def refresh_pdf_list(self):
        """Actualiza la lista de PDFs disponibles en el dropdown"""
        try:
            stats = self.chatbot.rag.get_stats()
            available_pdfs = stats.get('pdfs', [])

            # Actualizar dropdown con los PDFs disponibles
            self.pdf_dropdown.options = [
                ft.dropdown.Option(pdf) for pdf in available_pdfs
            ]

            # Si hay solo un PDF, seleccionarlo automáticamente
            if len(available_pdfs) == 1:
                self.pdf_dropdown.value = available_pdfs[0]
                self.current_pdf = available_pdfs[0]

            self.pdf_dropdown.update()
            self.available_pdfs = available_pdfs
        except Exception as ex:
            print(f"Error actualizando lista de PDFs: {ex}")

    def clear_chat(self, e):
        self.chatbot.clear_chat_history()
        self.chat_display.controls.clear()
        self.chat_display.update()
        self.add_message_to_display("✅ Sistema", "Chat limpiado", is_user=False)

    def clear_database(self, e):
        try:
            self.chatbot.rag.clear_database()
            self.current_pdf = None  # Resetear el PDF actual
            self.pdf_dropdown.value = None  # Limpiar selector
            self.pdf_dropdown.options = []
            self.pdf_dropdown.update()
            self.add_message_to_display(
                "✅ Sistema",
                "Base de datos limpiada completamente\n💡 Todos los PDFs han sido eliminados",
                is_user=False
            )
            self.update_stats()
        except Exception as ex:
            self.add_message_to_display("❌ Error", f"Error limpiando BD: {str(ex)}", is_user=False)

    def show_stats(self, e):
        try:
            stats = self.chatbot.rag.get_stats()
            pdfs_list = "\n".join([f"  • {pdf}" for pdf in stats.get('pdfs', [])])
            if not pdfs_list:
                pdfs_list = "  (ninguno)"

            stats_msg = f"""
📊 Estadísticas del Sistema
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Chunks en BD: {stats['total_chunks']}
📄 PDFs almacenados: {stats.get('total_pdfs', 0)}
🧠 Modelo: {stats['embedding_model']}
💾 Ruta: {stats['database_path']}

📋 PDFs en la BD:
{pdfs_list}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """.strip()
            self.add_message_to_display("📊 Estadísticas", stats_msg, is_user=False)
        except Exception as ex:
            self.add_message_to_display("❌ Error", f"No se pueden obtener estadísticas: {str(ex)}", is_user=False)

    def update_stats(self):
        try:
            stats = self.chatbot.rag.get_stats()
            pdf_count = stats.get('total_pdfs', 0)
            provider = self.chatbot.provider.capitalize()
            self.stats_text.value = f"🤖 {provider} | 📚 PDFs: {pdf_count} | Chunks: {stats['total_chunks']}"
            self.refresh_pdf_list()
        except:
            self.stats_text.value = " Estado: Listo"
        self.stats_text.update()


if __name__ == "__main__":
    gui = ChatbotGUI()
    ft.app(target=gui.main)
