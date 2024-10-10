from flask import Flask, request, jsonify
from collections import deque
import json
import threading
import time
import uuid
import spacy
from fuzzywuzzy import process

app = Flask(__name__)

# A dictionary to store the status of tasks
tasks = {}

# Load the knowledge graph
with open('kg.json', 'r') as f:
    knowledge_graph = json.load(f)

# Load Spacy's NER model (assuming you're using English)
nlp = spacy.load("en_core_web_sm")


# Simulated long-running task
def my_heavy_task(task_id, question, graph):
    time.sleep(10)  # Simulate a long-running task
    tasks[task_id]['status'] = 'finished'
    tasks[task_id]['result'] = "Task completed"


@app.route('/entity-info', methods=['GET'])
def get_entity_info():
    entity = request.args.get('entity')
    node_info = [node for node in knowledge_graph['nodes'] if node['name'] == entity]
    
    if node_info:
        return jsonify(node_info)
    else:
        return jsonify({'error': 'Entity not found'}), 404


@app.route('/supplier-products', methods=['GET'])
def get_supplier_products():
    supplier_name = request.args.get('supplier')

    # Step 1: Find supplier node by name
    supplier = next((node['id'] for node in knowledge_graph['nodes'] if node['type'] == 'Supplier' and node['name'] == supplier_name), None)
    
    if not supplier:
        return jsonify({'error': f'Supplier {supplier_name} not found'}), 404

    # Step 2: Find manufacturers that the supplier provides materials to
    supplied_manufacturers = [edge['target'] for edge in knowledge_graph['edges'] if edge['source'] == supplier and edge['relationship'] == 'supplies']

    # Step 3: Find products produced by these manufacturers
    products = []
    for manufacturer in supplied_manufacturers:
        produced_products = [edge['target'] for edge in knowledge_graph['edges'] if edge['source'] == manufacturer and edge['relationship'] == 'produces']
        products.extend(produced_products)

    # Get product names
    product_names = [node['name'] for node in knowledge_graph['nodes'] if node['id'] in products]

    if product_names:
        return jsonify({'supplier': supplier_name, 'products': product_names})
    else:
        return jsonify({'error': f'No products found for supplier {supplier_name}'}), 404



@app.route('/products-location', methods=['GET'])
def get_products_in_location():
    location = request.args.get('location')

    # Step 1: Find suppliers or manufacturers in the given location
    suppliers_in_location = [node['id'] for node in knowledge_graph['nodes'] if node.get('attributes', {}).get('location') == location and node['type'] == 'Supplier']
    manufacturers_in_location = [node['id'] for node in knowledge_graph['nodes'] if node.get('attributes', {}).get('location') == location and node['type'] == 'Manufacturer']
    
    # Step 2: Find products associated with suppliers or manufacturers in this location
    products = []
    
    # Find products produced by manufacturers in the location
    for manufacturer in manufacturers_in_location:
        produced_products = [edge['target'] for edge in knowledge_graph['edges'] if edge['source'] == manufacturer and edge['relationship'] == 'produces']
        products.extend(produced_products)
    
    # Find products indirectly associated through suppliers (suppliers -> manufacturers -> products)
    for supplier in suppliers_in_location:
        supplied_manufacturers = [edge['target'] for edge in knowledge_graph['edges'] if edge['source'] == supplier and edge['relationship'] == 'supplies']
        for manufacturer in supplied_manufacturers:
            produced_products = [edge['target'] for edge in knowledge_graph['edges'] if edge['source'] == manufacturer and edge['relationship'] == 'produces']
            products.extend(produced_products)

    # Return products found for the given location
    if products:
        product_names = [node['name'] for node in knowledge_graph['nodes'] if node['id'] in products]
        return jsonify({'location': location, 'products': product_names})
    else:
        return jsonify({'error': f'No products found for location {location}'}), 404




@app.route('/natural-disaster-impact', methods=['GET'])
def get_disaster_impact():
    city = request.args.get('city')

    # Step 1: Find suppliers in the given city
    affected_suppliers = [node['id'] for node in knowledge_graph['nodes'] if node.get('attributes', {}).get('location') == city and node['type'] == 'Supplier']
    
    # Step 2: Find products associated with these suppliers (through manufacturers)
    affected_products = []
    for supplier in affected_suppliers:
        supplied_manufacturers = [edge['target'] for edge in knowledge_graph['edges'] if edge['source'] == supplier and edge['relationship'] == 'supplies']
        for manufacturer in supplied_manufacturers:
            produced_products = [edge['target'] for edge in knowledge_graph['edges'] if edge['source'] == manufacturer and edge['relationship'] == 'produces']
            affected_products.extend(produced_products)

    # Get product names
    affected_product_names = [node['name'] for node in knowledge_graph['nodes'] if node['id'] in affected_products]

    return jsonify({
        'city': city,
        'affected_suppliers': [node['name'] for node in knowledge_graph['nodes'] if node['id'] in affected_suppliers],
        'affected_products': affected_product_names
    })



@app.route('/ask-question', methods=['POST'])
def ask_question():
    question = request.json.get('question')
    
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'in-progress', 'result': None}

    # Start the heavy task in a new thread
    thread = threading.Thread(target=my_heavy_task, args=(task_id, question, None))
    thread.start()

    return jsonify({'task_id': task_id}), 202


@app.route('/relationship', methods=['GET'])
def get_relationship():
    node1_name = request.args.get('node1')
    node2_name = request.args.get('node2')

    # Step 1: Find node IDs by name
    node1 = next((node['id'] for node in knowledge_graph['nodes'] if node['name'] == node1_name), None)
    node2 = next((node['id'] for node in knowledge_graph['nodes'] if node['name'] == node2_name), None)

    if not node1 or not node2:
        return jsonify({'error': f'Nodes {node1_name} or {node2_name} not found'}), 404

    # Step 2: Use BFS or DFS to find the shortest path between node1 and node2
    def bfs(graph, start, end):
        queue = deque([(start, [])])
        visited = set()

        while queue:
            current, path = queue.popleft()
            if current == end:
                return path + [current]
            if current not in visited:
                visited.add(current)
                # Add neighbors to the queue (both directions in the graph)
                neighbors = [edge['target'] for edge in graph['edges'] if edge['source'] == current] + \
                            [edge['source'] for edge in graph['edges'] if edge['target'] == current]
                for neighbor in neighbors:
                    queue.append((neighbor, path + [current]))
        return None

    # Step 3: Find the path between node1 and node2
    path = bfs(knowledge_graph, node1, node2)
    if path:
        path_names = [node['name'] for node in knowledge_graph['nodes'] if node['id'] in path]
        return jsonify({'path': path_names})
    else:
        return jsonify({'error': f'No relationship found between {node1_name} and {node2_name}'}), 404
    

# Endpoint to check task status
@app.route('/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = tasks.get(task_id)
    if task:
        return jsonify(task)
    else:
        return jsonify({'error': 'Task not found'}), 404


@app.route('/extract-entities', methods=['POST'])
def extract_entities():
    text = request.json.get('text')

    # Step 1: Use Spacy's NLP model to extract entities from the text
    doc = nlp(text)
    extracted_entities = [ent.text for ent in doc.ents]  # Extract named entities

    # Step 2: Match extracted entities with the knowledge graph using fuzzy matching
    matched_entities = []

    for entity in extracted_entities:
        # Use fuzzy matching to find the closest match in the graph
        graph_entity_names = [node['name'] for node in knowledge_graph['nodes']]
        best_match, score = process.extractOne(entity, graph_entity_names)

        if score > 80:  # Only keep good matches
            matched_entities.append({'extracted_entity': entity, 'matched_entity': best_match, 'confidence': score})

    return jsonify({'text': text, 'matched_entities': matched_entities})


if __name__ == '__main__':
    app.run(debug=True)
