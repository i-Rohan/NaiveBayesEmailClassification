from tkinter import *

root = Tk()
root.configure(background="#f3f3f3")
root.title("Naive Bayes Email Classifier")
root.geometry("1366x768")
# root.wm_iconbitmap("spam.ico")

label = Label(root, background="#e74c3c", text="Naive Bayes Email Classification", )
label.config(font=("Times", 40), fg="#ffffff")
label.pack(fill="x")

list_ = [x * 5 for x in range(0, 100000, 1)]
l1 = Listbox(root, height=768, width=1366)
for i in list_:
    l1.insert(END, i)
l1.pack()
label.pack()

root.mainloop()
