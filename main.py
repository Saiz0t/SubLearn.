import customtkinter as ctk
from tkinter import messagebox
import re
import threading
import os
import random
from translate import Translator

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class SublearnApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sublearn")
        self.geometry("600x600")

        self.translator = Translator(from_lang="en", to_lang="ru")
        self.flashcards = []
        self.current_card_index = 0
        self.file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sublearn_cards.txt")

        self.show_main_menu()

    def show_main_menu(self):
        for widget in self.winfo_children(): widget.destroy()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=20)
        ctk.CTkLabel(header_frame, text="SUBLEARN", font=("Arial Bold", 42), text_color="#3B8ED0").pack()
        ctk.CTkLabel(header_frame, text="режим викторины", font=("Arial", 18), text_color="gray").pack()

        btn_style = {"width": 300, "height": 60, "font": ("Arial Bold", 18), "corner_radius": 15}
        ctk.CTkButton(self, text="Начать тест", command=self.start_cards_mode, **btn_style).grid(row=1, column=0,
                                                                                                 pady=10)
        ctk.CTkButton(self, text="Загрузить субтитры", command=self.start_processing, **btn_style).grid(row=2, column=0,
                                                                                                        pady=10)

    
    def start_processing(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("Subtitle files", "*.srt")])
        if path:
            threading.Thread(target=self.process_logic, args=(path,), daemon=True).start()

    def process_logic(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            clean_text = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', '', raw_text)
            words = re.findall(r'\b[a-zA-Z]{4,}\b', clean_text.lower())
            unique_words = sorted(list(set(words)))[:30]

            word_data = []
            for word in unique_words:
                try:
                    res = self.translator.translate(word)
                    
                    if res and "[ошибка" not in res.lower() and "MYMEMORY" not in res:
                        word_data.append((word, res))
                        print(f"Успешно: {word} -> {res}")
                except:
                    print(f"Пропущено (ошибка сети): {word}")
                    continue  # Просто идем к следующему слову

            if not word_data:
                self.after(0, lambda: messagebox.showwarning("Внимание",
                                                             "Не удалось перевести ни одного слова. Проверьте интернет!"))
                return

            with open(self.file_path, 'w', encoding='utf-8') as f:
                for w, t in word_data:
                    f.write(f"{w};{t}\n")

            self.after(0, lambda: messagebox.showinfo("Успех", f"Готово! Сохранено слов: {len(word_data)}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Ошибка", f"{e}"))
 
    def start_cards_mode(self):
        if not os.path.exists(self.file_path):
            messagebox.showwarning("Внимание", "Сначала создайте файл!")
            return
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.flashcards = [line.strip().split(';') for line in f if ';' in line]
            if len(self.flashcards) < 3:
                messagebox.showwarning("Мало слов", "Нужно хотя бы 3 слова для теста!")
                return
            random.shuffle(self.flashcards)
            self.current_card_index = 0
            self.show_test_ui()
        except Exception as e:
            messagebox.showerror("Ошибка", f"{e}")

    def show_test_ui(self):
        for widget in self.winfo_children(): widget.destroy()

        self.word_label = ctk.CTkLabel(self, text="", font=("Arial Bold", 38), text_color="white")
        self.word_label.pack(pady=(50, 30))

        # Кнопки вариантов
        self.answer_buttons = []
        for i in range(3):
            btn = ctk.CTkButton(
                self, text="", width=350, height=55,font=("Arial", 16), corner_radius=10,
                command=lambda idx=i: self.check_answer(idx)
            )
            btn.pack(pady=10)
            self.answer_buttons.append(btn)

        # Управление
        ctk.CTkButton(self, text="В меню", command=self.show_main_menu, fg_color="transparent", border_width=1).pack(pady=30)

        self.load_question()

    def load_question(self):
        for btn in self.answer_buttons:
            btn.configure(fg_color=["#3B8ED0", "#1f538d"])

        correct_word, self.correct_ans = self.flashcards[self.current_card_index]
        self.word_label.configure(text=correct_word.upper())

        other_cards = [c for c in self.flashcards if c[1] != self.correct_ans]
        wrong_options = random.sample(other_cards, 2)

        self.options = [self.correct_ans, wrong_options[0][1], wrong_options[1][1]]
        random.shuffle(self.options)

        for i in range(3):
            self.answer_buttons[i].configure(text=self.options[i])

    def check_answer(self, idx):
        selected = self.options[idx]
        if selected == self.correct_ans:
            self.answer_buttons[idx].configure(fg_color="green")
            self.after(800, self.next_question) # Задержка перед следующим вопросом
        else:
            self.answer_buttons[idx].configure(fg_color="red")

    def next_question(self):
        self.current_card_index = (self.current_card_index + 1) % len(self.flashcards)
        self.load_question()

if __name__ == "__main__":
    app = SublearnApp()
    app.mainloop()
