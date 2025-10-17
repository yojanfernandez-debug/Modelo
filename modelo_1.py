from flask import Flask, request, render_template
from pulp import *

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def resolver_bauxita():
    # Conjuntos
    MINAS = ["A", "B", "C"]
    PLALU = ["B", "C", "D", "E"]
    PLESM = ["D", "E"]

    # Parámetros base
    capbaux = {"A":36000,"B":52000,"C":28000}
    capb_al = {"B":40000,"C":20000,"D":30000,"E":80000}
    capal_es = {"D":4000,"E":7000}
    demanda = {"D":1000,"E":1200}

    cexp = {"A":420,"B":360,"C":540}
    cpal = {"B":330,"C":320,"D":380,"E":240}
    cpes = {"D":8500,"E":5200}
    ctran_b = {
        ("A","B"):400, ("A","C"):2010, ("A","D"):510, ("A","E"):1920,
        ("B","B"):10, ("B","C"):630, ("B","D"):220, ("B","E"):1510,
        ("C","B"):1630, ("C","C"):10, ("C","D"):620, ("C","E"):940,
    }
    ctran_al = {
        ("B","D"):220, ("B","E"):1510,
        ("C","D"):620, ("C","E"):940,
        ("D","D"):0,   ("D","E"):1615,
        ("E","D"):1465,("E","E"):0
    }
    rendal = {"A":0.060,"B":0.080,"C":0.062}
    rendim = 0.4

    # Verificar si se ha enviado el formulario
    if request.method == 'POST':
        # Obtener los costos desde el formulario
        try:
            costo_1 = float(request.form.get('costo_1', 0))
            costo_2 = float(request.form.get('costo_2', 0))
            costo_3 = float(request.form.get('costo_3', 0))
            costo_4 = float(request.form.get('costo_4', 0))
        except ValueError:
            return "Por favor ingresa solo valores numéricos válidos."

        # Crear diccionario de costos fijos (uno por planta)
        cfijo = {
            "B": costo_1,
            "C": costo_2,
            "D": costo_3,
            "E": costo_4
        }

        # Modelo de optimización
        modelo = LpProblem("Problema_Bauxita", LpMinimize)

        # Variables
        x = LpVariable.dicts("x", [(i,j) for i in MINAS for j in PLALU], lowBound=0)
        y = LpVariable.dicts("y", [(j,k) for j in PLALU for k in PLESM], lowBound=0)
        w = LpVariable.dicts("w", PLALU, cat="Binary")

        # Función objetivo
        modelo += (
            lpSum(cexp[i]*x[(i,j)] for i in MINAS for j in PLALU)
            + lpSum(cpal[j]*y[(j,k)] for j in PLALU for k in PLESM)
            + lpSum(cpes[k]*y[(j,k)] for j in PLALU for k in PLESM)
            + lpSum(ctran_b[(i,j)]*x[(i,j)] for i in MINAS for j in PLALU)
            + lpSum(ctran_al[(j,k)]*y[(j,k)] for j in PLALU for k in PLESM)
            + lpSum(cfijo[j]*w[j] for j in PLALU)
        )

        # Restricciones
        for i in MINAS:
            modelo += lpSum(x[(i,j)] for j in PLALU) <= capbaux[i]
        for j in PLALU:
            modelo += lpSum(x[(i,j)] for i in MINAS) <= capb_al[j] * w[j]
        for k in PLESM:
            modelo += lpSum(y[(j,k)] for j in PLALU) <= capal_es[k]
        for k in PLESM:
            modelo += lpSum(rendim * y[(j,k)] for j in PLALU) == demanda[k]
        for j in PLALU:
            modelo += lpSum(rendal[i]*x[(i,j)] for i in MINAS) == lpSum(y[(j,k)] for k in PLESM)

        # Resolver el modelo
        modelo.solve()

        # Resultados
        funcion_objetivo = value(modelo.objective)
        dato1 = w['B'].varValue
        dato2 = w['C'].varValue
        dato3 = w['D'].varValue
        dato4 = w['E'].varValue

        return render_template(
            "bauxita.html",
            funcion_objetivo=funcion_objetivo,
            dato1=dato1, dato2=dato2, dato3=dato3, dato4=dato4,
            cfijo=cfijo
        )

    
    return render_template("bauxita.html", funcion_objetivo=None, cfijo=None)


if __name__ == "__main__":
    app.run(debug=True)    # Ejecutar servidor

