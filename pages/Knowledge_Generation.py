# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "neo4j",
#     "pydantic",
# ]
# ///

# main_streamlit_app.py
import streamlit as st
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, ValidationError
from neo4j import GraphDatabase, basic_auth
import json

# --- 1. Conceptual Ontology & Pydantic Models ---
# (Same Pydantic models as before)

class BaseNode(BaseModel):
    id: str = Field(..., description="Unique identifier for the node (e.g., name, official ID).")
    type: str = Field(..., description="Type of the node (e.g., 'Well', 'Formation').")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Key-value properties of the node.")

    @validator('id', pre=True, always=True)
    def sanitize_id(cls, v):
        return str(v).replace(" ", "_").replace("/", "_").replace(":", "_")

class Well(BaseNode):
    type: str = "Well"
    wellbore_name: Optional[str] = None
    purpose: Optional[str] = None
    completion_date: Optional[str] = None
    total_depth_m: Optional[float] = None
    water_depth_m: Optional[float] = None

class Formation(BaseNode):
    type: str = "Formation"
    geologic_age: Optional[str] = None
    lithology_description: Optional[str] = None

class Field(BaseNode):
    type: str = "Field"
    discovery_year: Optional[int] = None
    status: Optional[str] = None

class License(BaseNode):
    type: str = "License"
    awarded_date: Optional[str] = None
    valid_until_date: Optional[str] = None

class Company(BaseNode):
    type: str = "Company"
    country_of_registration: Optional[str] = None

class Relationship(BaseModel):
    source_id: str
    source_type: str
    target_id: str
    target_type: str
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    @validator('source_id', 'target_id', pre=True, always=True)
    def sanitize_ids_in_relationship(cls, v):
        return str(v).replace(" ", "_").replace("/", "_").replace(":", "_")

class KnowledgeGraphData(BaseModel):
    nodes: List[BaseNode]
    relationships: List[Relationship]

# --- 2. LLM-supported NER (Simulated Output) ---
EXAMPLE_INPUT_TEXT = """
The Statfjord field, discovered in 1974, is a major oil and gas field in the Norwegian sector of the North Sea.
Well 33/9-A-12, completed on 1980-05-15, targets the Brent Formation within production license PL037.
PL037 is operated by Equinor ASA. The Brent Formation is of Middle Jurassic age and primarily consists of sandstone.
"""

MOCK_LLM_OUTPUT = {
    "nodes": [
        {"id": "Statfjord Field", "type": "Field", "attributes": {"discovery_year": 1974, "status": "Producing", "location": "Norwegian North Sea"}},
        {"id": "33/9-A-12", "type": "Well", "attributes": {"wellbore_name": "33/9-A-12 H", "purpose": "Production", "completion_date": "1980-05-15", "total_depth_m": 3000.0}},
        {"id": "Brent Formation", "type": "Formation", "attributes": {"geologic_age": "Middle Jurassic", "lithology_description": "Primarily sandstone"}},
        {"id": "PL037", "type": "License", "attributes": {"awarded_date": "1975-01-01"}},
        {"id": "Equinor ASA", "type": "Company", "attributes": {"country_of_registration": "Norway"}}
    ],
    "relationships": [
        {"source_id": "33/9-A-12", "source_type": "Well", "target_id": "Brent Formation", "target_type": "Formation", "relationship_type": "TARGETS_FORMATION", "properties": {"confidence_score": 0.95}},
        {"source_id": "33/9-A-12", "source_type": "Well", "target_id": "Statfjord Field", "target_type": "Field", "relationship_type": "IS_IN_FIELD", "properties": {}},
        {"source_id": "33/9-A-12", "source_type": "Well", "target_id": "PL037", "target_type": "License", "relationship_type": "DRILLED_IN_LICENSE", "properties": {}},
        {"source_id": "PL037", "source_type": "License", "target_id": "Equinor ASA", "target_type": "Company", "relationship_type": "OPERATED_BY", "properties": {"operator_share_percentage": 45.0}},
        {"source_id": "Statfjord Field", "source_type": "Field", "target_id": "PL037", "target_type": "License", "relationship_type": "ASSOCIATED_WITH_LICENSE", "properties": {}}
    ]
}

# --- 3. Pydantic Validation Function ---
def parse_and_validate_llm_output(llm_json_output: Dict) -> Optional[KnowledgeGraphData]:
    try:
        parsed_nodes = []
        for node_data in llm_json_output.get("nodes", []):
            node_type = node_data.get("type")
            attributes = node_data.get("attributes", {})
            node_id = node_data.get("id")
            common_data = {"id": node_id, "attributes": attributes}

            # Dynamically assign specific fields if they exist in Pydantic model and attributes
            specific_model_map = {
                "Well": Well, "Formation": Formation, "Field": Field,
                "License": License, "Company": Company
            }
            model_class = specific_model_map.get(node_type, BaseNode)
            
            specific_fields_data = {}
            # Iterate through fields of the specific model (e.g., Well)
            # and pop them from 'attributes' if they are present, to avoid duplication.
            if model_class != BaseNode:
                for field_name in model_class.__fields__:
                    if field_name in attributes and field_name not in BaseNode.__fields__:
                        specific_fields_data[field_name] = attributes.pop(field_name)
            
            # Create the node instance
            if model_class == BaseNode and node_type not in specific_model_map:
                 st.warning(f"Unknown node type '{node_type}' for id '{node_id}'. Using BaseNode.")
                 parsed_nodes.append(BaseNode(id=node_id, type=node_type or "Unknown", attributes=attributes))
            else:
                # Pass common_data, specific_fields_data, and remaining attributes
                # Ensure 'type' is explicitly passed if model_class is BaseNode but type is known
                if model_class == BaseNode:
                     parsed_nodes.append(model_class(**common_data, type=node_type, **specific_fields_data))
                else:
                     parsed_nodes.append(model_class(**common_data, **specific_fields_data))


        parsed_relationships = [Relationship(**rel_data) for rel_data in llm_json_output.get("relationships", [])]
        kg_data = KnowledgeGraphData(nodes=parsed_nodes, relationships=parsed_relationships)
        return kg_data
    except ValidationError as e:
        st.error(f"Pydantic Validation Error: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during parsing: {e}")
        return None

# --- 4. Neo4j Integration ---
class Neo4jUploader:
    def __init__(self, uri, user, password):
        try:
            self._driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
            self._driver.verify_connectivity() # Check connection
            st.success("Successfully connected to Neo4j.")
        except Exception as e:
            st.error(f"Neo4j Connection Error: {e}")
            self._driver = None # Ensure driver is None if connection fails
            raise # Re-raise the exception to be caught by the caller

    def close(self):
        if self._driver:
            self._driver.close()

    def upload_kg_data(self, kg_data: KnowledgeGraphData):
        if not self._driver:
            st.error("Neo4j driver not initialized. Cannot upload data.")
            return False
        
        uploaded_nodes_count = 0
        uploaded_rels_count = 0
        try:
            with self._driver.session() as session:
                for node in kg_data.nodes:
                    session.execute_write(self._create_node_tx, node)
                    uploaded_nodes_count +=1
                for rel in kg_data.relationships:
                    session.execute_write(self._create_relationship_tx, rel)
                    uploaded_rels_count +=1
            st.success(f"Data uploaded to Neo4j: {uploaded_nodes_count} nodes, {uploaded_rels_count} relationships.")
            return True
        except Exception as e:
            st.error(f"Error during Neo4j upload: {e}")
            return False

    @staticmethod
    def _create_node_tx(tx, node: BaseNode):
        query = (
            f"MERGE (n:{node.type} {{id: $id}}) "
            "SET n += $node_props "
        )
        
        # Prepare node properties for Neo4j
        # Start with the generic 'attributes' field
        node_props = node.attributes.copy() if node.attributes else {}
        # Add specific Pydantic fields to the properties, overriding if necessary
        for field_name, field_value in node.model_dump().items():
            if field_name not in ['id', 'type', 'attributes'] and field_value is not None:
                node_props[field_name] = field_value
        
        # Remove None values from final properties to avoid setting null properties explicitly
        node_props = {k: v for k, v in node_props.items() if v is not None}
        
        params = {"id": node.id, "node_props": node_props}
        # st.write(f"Executing Node Query: MERGE (n:{node.type} {{id: '{node.id}'}}) SET n += {json.dumps(node_props)}") # For debugging
        tx.run(query, **params)

    @staticmethod
    def _create_relationship_tx(tx, rel: Relationship):
        query = (
            f"MATCH (source:{rel.source_type} {{id: $source_id}}) "
            f"MATCH (target:{rel.target_type} {{id: $target_id}}) "
            f"MERGE (source)-[r:{rel.relationship_type}]->(target) "
            "SET r += $properties"
        )
        params = {
            "source_id": rel.source_id,
            "target_id": rel.target_id,
            "properties": {k: v for k, v in rel.properties.items() if v is not None} # Clean None values
        }
        # st.write(f"Executing Relationship Query for type: {rel.relationship_type}") # For debugging
        tx.run(query, **params)

# --- Streamlit UI ---
st.set_page_config(page_title="Oil & Gas KG Pipeline (Norway Subsurface)", layout="wide")

st.title("🛢️ Oil & Gas Knowledge Graph Pipeline")
st.caption("Norway Subsurface Domain - LLM, Pydantic, Neo4j Integration Demo")

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("🔩 Neo4j Configuration")
    st.info("Update these details to connect to your Neo4j instance.")
    default_uri = st.session_state.get("neo4j_uri", "bolt://localhost:7687")
    default_user = st.session_state.get("neo4j_user", "neo4j")
    default_password = st.session_state.get("neo4j_password", "your_neo4j_password")

    neo4j_uri = st.text_input("Neo4j URI", value=default_uri)
    neo4j_user = st.text_input("Neo4j User", value=default_user)
    neo4j_password = st.text_input("Neo4j Password", type="password", value=default_password)

    # Store in session state to persist across reruns if needed for other interactions
    st.session_state.neo4j_uri = neo4j_uri
    st.session_state.neo4j_user = neo4j_user
    st.session_state.neo4j_password = neo4j_password
    
    st.markdown("---")
    st.header("ℹ️ About")
    st.markdown("""
    This application demonstrates a conceptual pipeline for building a Knowledge Graph:
    1.  **LLM-NER (Simulated):** Extracts entities & relationships from text.
    2.  **Pydantic Validation:** Ensures data quality and schema adherence.
    3.  **Neo4j Storage:** Loads the structured data into a graph database.
    """)

# --- Main Application Flow ---

# Section 1: Conceptual Schema (Pydantic Models)
st.header("1. Conceptual Schema (Pydantic Models)")
with st.expander("View Pydantic Model Definitions (Schema)"):
    st.markdown("""
    The following Pydantic models define the expected structure for our knowledge graph entities and relationships.
    This acts as our schema, inspired by RDF/OWL principles.
    """)
    models_code = """
class BaseNode(BaseModel):
    id: str
    type: str
    attributes: Dict[str, Any]

class Well(BaseNode): type = "Well"; wellbore_name: Optional[str]; ...
class Formation(BaseNode): type = "Formation"; geologic_age: Optional[str]; ...
class Field(BaseNode): type = "Field"; discovery_year: Optional[int]; ...
class License(BaseNode): type = "License"; awarded_date: Optional[str]; ...
class Company(BaseNode): type = "Company"; country_of_registration: Optional[str]; ...

class Relationship(BaseModel):
    source_id: str; source_type: str
    target_id: str; target_type: str
    relationship_type: str
    properties: Dict[str, Any]

class KnowledgeGraphData(BaseModel):
    nodes: List[BaseNode]
    relationships: List[Relationship]
    """
    st.code(models_code, language="python")

# Section 2: LLM Input and Simulated Output
st.header("2. LLM-NER Processing (Simulated)")
st.subheader("Example Input Text for LLM")
st.text_area("Input Text", EXAMPLE_INPUT_TEXT, height=150, disabled=True)

st.subheader("Simulated LLM JSON Output")
with st.expander("View Simulated LLM JSON"):
    st.json(MOCK_LLM_OUTPUT)

# Initialize validated_kg_data in session state
if 'validated_kg_data' not in st.session_state:
    st.session_state.validated_kg_data = None

# Section 3: Pydantic Validation
st.header("3. Pydantic Validation")
if st.button("🔍 Validate LLM Output"):
    with st.spinner("Validating data..."):
        st.session_state.validated_kg_data = parse_and_validate_llm_output(MOCK_LLM_OUTPUT)
        if st.session_state.validated_kg_data:
            st.success("Pydantic validation successful!")
        # Errors are handled within the function by st.error

if st.session_state.validated_kg_data:
    st.subheader("Validated Knowledge Graph Data")
    with st.expander("View Validated Data (Pydantic Models as JSON)"):
        # Convert Pydantic models to dicts for JSON serialization
        display_data = {
            "nodes": [node.model_dump() for node in st.session_state.validated_kg_data.nodes],
            "relationships": [rel.model_dump() for rel in st.session_state.validated_kg_data.relationships]
        }
        st.json(display_data)
else:
    st.info("Click 'Validate LLM Output' to see results.")


# Section 4: Neo4j Upload
st.header("4. Neo4j Upload")
if st.session_state.validated_kg_data:
    if st.button("🚀 Upload Validated Data to Neo4j"):
        if not neo4j_uri or not neo4j_user or not neo4j_password:
            st.warning("Please provide Neo4j connection details in the sidebar.")
        else:
            uploader = None
            try:
                with st.spinner("Connecting to Neo4j and uploading data..."):
                    uploader = Neo4jUploader(neo4j_uri, neo4j_user, neo4j_password)
                    if uploader._driver: # Check if driver was successfully initialized
                        success = uploader.upload_kg_data(st.session_state.validated_kg_data)
                        if success:
                            st.balloons()
                            st.markdown("---")
                            st.subheader("🔎 Example Neo4j Queries")
                            st.code("MATCH (n) RETURN n LIMIT 25;", language="cypher")
                            st.code("MATCH (w:Well)-[:TARGETS_FORMATION]->(f:Formation) RETURN w, f;", language="cypher")
                            st.code("MATCH p=()-[r]->() RETURN p LIMIT 50;", language="cypher")
            except Exception as e:
                # Error already displayed by Neo4jUploader init or upload_kg_data
                # st.error(f"An error occurred: {e}") # Redundant if already handled
                pass # Errors are displayed within Neo4jUploader
            finally:
                if uploader:
                    uploader.close()
                    # st.info("Neo4j connection closed.") # Can be a bit noisy
else:
    st.warning("Data must be validated successfully before it can be uploaded to Neo4j.")

st.markdown("---")
st.markdown("End of Demo Application.")

if __name__ in ("__main__", "__page__"):
    main()
