import subprocess
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from serial_coms import *


def clicked_cb3():
    if entry.cget('show') == '':
        entry.config(show='*')
        clicked_cb3.config(text='Show Password')
    else:
        entry.config(show='')
        clicked_cb3.config(text='Hide Password')


def clicked_cb4():
    if entry1.cget('show') == '':
        entry1.config(show='*')
        clicked_cb4.config(text='Show Password')
    else:
        entry1.config(show='')
        clicked_cb4.config(text='Hide Password')


def clicked_button1():
    messagebox.showinfo('Message', 'it loaded successfully')
    bt_module.test()


def clicked_button2():
    messagebox.showinfo('Message', 'Certificates are updated')


def clicked_delate():
    messagebox.askquestion(message='Are you sure')


def button1_clicked():
    pass


def button2_clicked():
    pass


def serial_clicked():
    pass


def list_serial_ports(evt):
    proc = subprocess.Popen(["ioreg -p IOUSB -w0 | sed 's/[^o]*o //; s/@.*$//' | grep -v '^Root.*'"],
                            stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    # print("program output:", out)
    devices = []
    for i in out.decode("utf-8").split('\n'):
        if i:
            print(i)
            #devices.append(i)
            listbox.insert(END, i)
    # listbox.insert(devices)
    '''
    w = evt.widget
    index = int(w.curselection()[0])
    value = w.get(index)
    print('You selected item %d: "%s"' % (index, value))
    '''

window = Tk()
window.title('read a data from USB')
window.minsize(width=1050, height=600)
window.configure(padx=30, pady=250, bg='#BDBDB7')

label1 = Label(text='CA certificate', bg='#BDBDB7')
label1.place(y=-80, x=10)
text_box1 = Text(width=70, height=7, bg='#DCDCDC')
text_box1.place(y=-55, x=10)
label2 = Label(text='Client certificate', bg='#BDBDB7')
label2.place(y=50, x=10)
text_box2 = Text(width=70, height=7, bg='#DCDCDC')
text_box2.place(y=76, x=10)
label3 = Label(text='Private key', bg='#BDBDB7')
label3.place(y=185, x=10)
text_box3 = Text(width=70, height=7, bg='#DCDCDC')
text_box3.place(y=210, x=10)

cb = Checkbutton(bg='#BDBDB7')
cb.place(y=-55, x=530)
cb1 = Checkbutton(bg='#BDBDB7')
cb1.place(y=76, x=530)
cb2 = Checkbutton(bg='#BDBDB7')
cb2.place(y=210, x=530)
cb3 = Checkbutton(bg='#BDBDB7', command=clicked_cb3)
cb3.place(y=-55, x=860)
cb4 = Checkbutton(bg='#BDBDB7', command=clicked_cb4)
cb4.place(y=76, x=860)

labelEntry = Label(text='Pre-shared key', bg='#BDBDB7')
labelEntry.place(y=-78, x=600)
entry = Entry(bg='#DCDCDC')
entry.place(y=-55, x=600, width=250)

labelEntry1 = Label(text='PSK identity', bg='#BDBDB7')
labelEntry1.place(y=50, x=600)
entry1 = Entry(bg='#DCDCDC')
entry1.place(y=74, x=600, width=250)

labelEntry2 = Label(text='Security Tag', bg='#BDBDB7')
labelEntry2.place(y=130, x=600)
entry2 = Entry(show='*', bg='#DCDCDC')
entry2.place(y=130, x=700, width=150)

head_txt_box = Canvas(width=950, height=120, bg='#DCDCDC')
head_txt_box.create_text(300, 50, text='this is canvas')
head_txt_box.place(y=-230, x=10)

hide_show = Label(text='hide\nshow\npassword', bg='#BDBDB7')
hide_show.place(y=-65, x=890)
hide_show = Label(text='hide\nshow\npassword', bg='#BDBDB7')
hide_show.place(y=65, x=890)

button1 = Button(text='load from JSON', activeforeground='green', command=clicked_button1)
button1.place(y=250, x=600, width=190)
button2 = Button(text='Update Certificates', activeforeground='blue', command=clicked_button2)
button2.place(y=250, x=800, width=160)
button3 = Button(text='Serial open', activeforeground='red', command=clicked_delate)
button3.place(y=280, x=600, width=360)

label_list_box = Label(window)
listbox = Listbox(window)
label_list_box.pack(side="bottom", fill="x")
listbox.pack(side="top", fill="both", expand=True)

listbox.bind("<<ListboxSelect>>", list_serial_ports)

#listbox.insert(["al", "ye"])
# window.mainloop()
