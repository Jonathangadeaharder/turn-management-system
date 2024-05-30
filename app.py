from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from flask_socketio import SocketIO, emit
import random
import time
from threading import Thread
from flask_caching import Cache
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Initialize the recent_change variable
recent_change = False

@app.route('/check_change')
def check_change():
    global recent_change
    response = {'recent_change': recent_change}
    if recent_change:
        recent_change = False  # Reset the change indicator
    return jsonify(response)
    
# Una lista para guardar los turnos solicitados por los clientes
turnos = []

# Una lista para guardar las mesas disponibles para los trabajadores
mesas = [1, 2]

# Una lista para guardar las asignaciones de turnos a las mesas
asignaciones = []

# Route for the main page
@app.route('/')
@cache.cached(timeout=31536000)  # 1 year in seconds
def index():
    # Redirigir a la pagina de solicitar turnos
    return redirect(url_for('solicitar_turnos'))

# Route for requesting turns
@app.route('/solicitar_turnos')
@cache.cached(timeout=31536000)  # 1 year in seconds
def solicitar_turnos():
    # Renderizar la pagina de solicitar turnos con los botones para elegir el servidor de internet
    return render_template('solicitar_turnos.html')

# Route for entering the DNI
@app.route('/ingresar_dni/<servidor>')
@cache.cached(timeout=31536000)  # 1 year in seconds
def ingresar_dni(servidor):
    # Renderizar la pagina para ingresar el dni con el teclado de numeros
    # El parametro servidor indica el servidor de internet elegido por el cliente
    return render_template('ingresar_dni.html', servidor=servidor)

# Route for confirming turn
@app.route('/confirmar_turno', methods=['POST'])
def confirmar_turno():
    # Obtener el dni y el servidor del formulario
    dni = request.form.get('dni')
    servidor = request.form.get('servidor')
    # Generar un numero aleatorio para el turno
    turno = random.randint(1000, 9999)
    # Agregar el turno, el dni y el servidor a la lista de turnos
    turnos.append((turno, dni, servidor))
    # Renderizar la pagina de confirmar turno con el mensaje de confirmacion
    return render_template('confirmar_turno.html', turno=turno, dni=dni, servidor=servidor)

# Route for accepting turns
@app.route('/aceptar_turnos/<mesa>')
def aceptar_turnos(mesa):
    # Renderizar la pagina de aceptar turnos con los turnos solicitados y el boton para aceptar
    # El parametro mesa indica la mesa del trabajador que accede a la pagina
    return render_template('aceptar_turnos.html', turnos=turnos, mesa=mesa)

@app.route('/asignar_turno/<mesa>/<turno>')
def asignar_turno(mesa, turno):
    global turnos, asignaciones, recent_change
    turno = int(turno)
    mesa = int(mesa)
    # Find and assign the turn to the specified table
    for t in turnos:
        if t[0] == turno:
            new_assignment = {
                'dni': t[1],
                'hora': t[2],
                'mesa': mesa
            }
            asignaciones.insert(0, new_assignment)  # Prepending to keep the most recent at the start
            if len(asignaciones) > 3:
                asignaciones.pop()  # Remove the oldest entry
            turnos.remove(t)
            recent_change = True  # Indicate that a new assignment has been added
            break
    return redirect(url_for('aceptar_turnos', mesa=mesa))

# Route for waiting screen
@app.route('/pantalla_de_espera')
def pantalla_de_espera():
    return render_template('pantalla_de_espera.html', asignaciones=asignaciones)

# Route for serving the sound file
@app.route('/sound.mp3')
def sound_mp3():
    return send_file('sound.mp3')

@app.route('/check_recent_change')
def check_recent_change():
    global recent_change
    response = jsonify({'recent_change': recent_change})
    recent_change = False  # Reset after checking
    return response

@app.route('/simulate_change')
def simulate_change():
    global recent_change
    recent_change = True
    return "Change simulated"
    
@app.route('/get_asignaciones')
def get_asignaciones():
    return jsonify(asignaciones)
    
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')
