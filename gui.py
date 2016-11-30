
from tkinter import *


root =Tk()
root.configure(background ="#f3f3f3")
root.title("Python project")
root.geometry("1200x800")
root.wm_iconbitmap("spam.ico")

label = Label(root,background = "#cc181e",text ="Spam classifier",)
label.config(font = ("Times",40))
label.pack(fill ="x")


list = [x*5 for x in range(0,1000000,1)]
l1 = Listbox()
for i in list:
    l1.insert( END ,i)
l1.pack()
label.pack()



root.mainloop()

