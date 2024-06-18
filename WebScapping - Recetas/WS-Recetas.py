#encoding:utf-8

from datetime import datetime
from bs4 import BeautifulSoup
import urllib.request
from tkinter import *
from tkinter import messagebox
import sqlite3
import lxml
import re
import locale


# lineas para evitar error SSL
import os, ssl
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


# Establecer el locale en español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

def cargar():
    respuesta = messagebox.askyesno(title="Confirmar",message="Esta seguro que quiere recargar los datos. \nEsta operación puede ser lenta")
    if respuesta:
        almacenar_bd()

def almacenar_bd():
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    conn.execute("DROP TABLE IF EXISTS RECETAS")
    conn.execute('''CREATE TABLE RECETAS
                 (TITULO            TEXT NOT NULL,
                 DIFICULTAD         TEXT,
                 COMENSALES         INT,
                 TIEMPO_PREP        TEXT,
                 AUTOR              TEXT,
                 FECHA_ACT          DATETIME);''')
    
    for receta in extraer_recetas():
        conn.execute("""INSERT INTO RECETAS VALUES (?,?,?,?,?,?)""",receta)
    
    conn.commit()
    cursor = conn.execute("SELECT COUNT(*) FROM RECETAS")
    messagebox.showinfo( "Base Datos", "Base de datos creada correctamente \nHay " + str(cursor.fetchone()[0]) + " registros")
    conn.close()


def extraer_recetas():
    lista_recetas = []
    url = "https://www.recetasgratis.net/Recetas-de-Aperitivos-tapas-listado_receta-1_1.html"
    f = urllib.request.urlopen(url)
    s = BeautifulSoup(f,"lxml")
    enlaces = s.find_all("div",class_="resultado link")

    for e in enlaces:
        titulo = e.a.string.strip()
        enlace_receta = e.a['href']
        f1 = urllib.request.urlopen(enlace_receta)
        j = BeautifulSoup(f1,"lxml")
       
        datos_autor = j.find_all("div", class_="nombre_autor")
        datos_receta = j.find_all("div", class_ ="recipe-info")
        for d in datos_autor:
            autor = d.a.string.strip()
            fecha_str = d.find("span", class_= "date_publish").string.strip()
            fecha_act = formatear_fecha(fecha_str)

        for r in datos_receta:
            comensales = r.find("span", class_="property comensales").string.strip()
            comensales = int(comensales.replace(" comensales",""))
            duracion = r.find("span", class_="property duracion").string.strip()   
            dificultad = r.find("span", class_="property dificultad").string.strip()
        lista_recetas.append((titulo,dificultad,comensales,duracion,autor,fecha_act))
    return lista_recetas

def listar_recetas():
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str  
    cursor = conn.execute("SELECT * FROM RECETAS")
    imprimir_lista(cursor)
    conn.close()

def imprimir_lista(cursor):      
    v = Toplevel()
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width=150, yscrollcommand=sc.set)
    for row in cursor:
        s = 'RECETA: ' + str(row[0])
        lb.insert(END, s)
        lb.insert(END, "------------------------------------------------------------------------")
        s = "     TITULO: " + str(row[0]) + " | DIFICULTAD: " + str(row[1]) + " | COMENSALES: " + str(row[2]) + " | TIEMPO PREPARACION: " + str(row[3]) + " | AUTOR: " + str(row[4]) + " | FECHA ACTUALIZACION: " + str(row[5])
        lb.insert(END, s)
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT, fill=BOTH)
    sc.config(command=lb.yview)

def imprimir_lista_autor(cursor,autor):
    v = Toplevel()
    v.title("RECETAS DE " + autor)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, width = 150, yscrollcommand=sc.set)
    for row in cursor:
        lb.insert(END,row[0])
        lb.insert(END,"    Autor: "+ row[4])
        lb.insert(END,"\n\n")
    lb.pack(side=LEFT,fill=BOTH)
    sc.config(command = lb.yview)


def buscar_por_autores():
    def listar(event):
            conn = sqlite3.connect('recetas.db')
            conn.text_factory = str
            cursor = conn.execute("SELECT TITULO, DIFICULTAD, COMENSALES, TIEMPO_PREP, AUTOR FROM RECETAS where AUTOR LIKE '%" + str(autor.get()) + "%'")
            conn.close
            imprimir_lista_autor(cursor,"AUTOR "+ autor.get().upper())
    conn = sqlite3.connect('recetas.db')
    conn.text_factory = str
    cursor = conn.execute("SELECT DISTINCT AUTOR FROM RECETAS")
    
    autores=set()
    for i in cursor:
        varios = i[0].split(",")
        for t in varios:
            autores.add(t.strip())

    v = Toplevel()
    label = Label(v,text="Seleccione el autor: ")
    label.pack(side=LEFT)
    autor = Spinbox(v, width= 30, values=list(autores))
    autor.bind("<Return>", listar)
    autor.pack(side=LEFT)
    
    conn.close()

def ventana_principal():
    root = Tk()
    root.geometry("150x100")

    menubar = Menu(root)
    
    datosmenu = Menu(menubar, tearoff=0)
    datosmenu.add_command(label="Cargar", command=almacenar_bd)
    datosmenu.add_separator()   
    datosmenu.add_command(label="Salir", command=root.quit)

    menubar.add_cascade(label="Datos", menu=datosmenu)

    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Recetas", command=listar_recetas)

    buscarmenu = Menu(menubar, tearoff=0)
    buscarmenu.add_command(label="Recetas por autores", command=buscar_por_autores)
    menubar.add_cascade(label="Buscar", menu=buscarmenu)
        
    root.config(menu=menubar)
    root.mainloop()


def formatear_fecha(fecha):
    fecha_strp = datetime.strptime(fecha.replace("Actualizado: ",""), "%d %B %Y")
    fecha_parseada = fecha_strp.strftime("%d/%m/%Y")
    return fecha_parseada

if __name__ == "__main__":
    ventana_principal()

