from flask import Flask, request, jsonify
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import threading
import time
import random

# Créer l'application Flask
app = Flask(__name__)

# 🔢 MÉTRIQUES PROMETHEUS
# Counter : ne peut qu'augmenter (parfait pour compter des événements)
REQUEST_COUNT = Counter(
    'flask_http_requests_total',          # Nom unique de la métrique
    'Nombre total de requêtes HTTP',      # Description humaine
    ['method', 'endpoint', 'status_code'] # Labels pour filtrer
)

# Histogram : mesure la distribution des valeurs (temps de réponse)
REQUEST_DURATION = Histogram(
    'flask_http_request_duration_seconds',
    'Durée des requêtes HTTP en secondes',
    ['method', 'endpoint']
)

# Gauge : valeur qui peut monter/descendre (utilisateurs connectés)
ACTIVE_USERS = Gauge(
    'flask_active_users',
    'Nombre d\'utilisateurs actifs actuellement'
)

# Counter pour les erreurs spécifiques
ERROR_COUNT = Counter(
    'flask_errors_total',
    'Nombre total d\'erreurs',
    ['error_type']
)

# Variable globale pour simuler des utilisateurs connectés
current_users = 0

# 🎯 ROUTES DE L'APPLICATION

@app.route("/")
def home():
    """Page d'accueil - simule une page normale"""
    start_time = time.time()  # Début du chronométrage
    
    try:
        # Simuler du travail (vraie logique métier ici)
        time.sleep(random.uniform(0.1, 0.3))  # Entre 100ms et 300ms
        
        # Incrémenter le compteur de requêtes (succès)
        REQUEST_COUNT.labels(
            method=request.method,    # GET, POST, etc.
            endpoint='/',             # Notre endpoint
            status_code='200'         # Code de succès
        ).inc()
        
        return jsonify({
            "message": "Bienvenue sur notre API !",
            "utilisateurs_connectes": current_users
        })
        
    except Exception as e:
        # En cas d'erreur, on l'enregistre aussi
        REQUEST_COUNT.labels(method=request.method, endpoint='/', status_code='500').inc()
        ERROR_COUNT.labels(error_type='internal_error').inc()
        raise
    
    finally:
        # Mesurer le temps total (même en cas d'erreur)
        duration = time.time() - start_time
        REQUEST_DURATION.labels(method=request.method, endpoint='/').observe(duration)

@app.route("/login", methods=['POST'])
def login():
    """Simule une connexion utilisateur"""
    global current_users
    start_time = time.time()
    
    try:
        # Simuler une authentification
        time.sleep(random.uniform(0.2, 0.5))
        
        # Augmenter le nombre d'utilisateurs connectés
        current_users += 1
        ACTIVE_USERS.set(current_users)  # Mettre à jour la gauge
        
        REQUEST_COUNT.labels(method='POST', endpoint='/login', status_code='200').inc()
        
        return jsonify({"status": "connecté", "utilisateurs_total": current_users})
    
    except Exception as e:
        REQUEST_COUNT.labels(method='POST', endpoint='/login', status_code='500').inc()
        ERROR_COUNT.labels(error_type='login_error').inc()
        raise
    
    finally:
        REQUEST_DURATION.labels(method='POST', endpoint='/login').observe(time.time() - start_time)

@app.route("/logout", methods=['POST'])
def logout():
    """Simule une déconnexion"""
    global current_users
    start_time = time.time()
    
    try:
        time.sleep(random.uniform(0.05, 0.1))
        
        # Diminuer le nombre d'utilisateurs
        current_users = max(0, current_users - 1)
        ACTIVE_USERS.set(current_users)
        
        REQUEST_COUNT.labels(method='POST', endpoint='/logout', status_code='200').inc()
        
        return jsonify({"status": "déconnecté", "utilisateurs_restants": current_users})
    
    finally:
        REQUEST_DURATION.labels(method='POST', endpoint='/logout').observe(time.time() - start_time)

@app.route("/error")
def simulate_error():
    """Route qui génère des erreurs pour tester le monitoring"""
    ERROR_COUNT.labels(error_type='simulated_error').inc()
    REQUEST_COUNT.labels(method='GET', endpoint='/error', status_code='500').inc()
    return jsonify({"error": "Erreur simulée pour le monitoring"}), 500

def start_metrics_server():
    """Démarre le serveur de métriques Prometheus sur le port 8000"""
    start_http_server(8000)
    print("🔍 Serveur de métriques démarré sur http://localhost:8000")

if __name__ == "__main__":
    # Démarrer le serveur de métriques en arrière-plan
    metrics_thread = threading.Thread(target=start_metrics_server)
    metrics_thread.daemon = True  # S'arrête quand l'app principale s'arrête
    metrics_thread.start()
    
    print("🚀 Application Flask démarrée sur http://localhost:5000")
    print("📊 Métriques disponibles sur http://localhost:8000/metrics")
    
    # Lancer Flask
    app.run(host="0.0.0.0", port=5000, debug=True)