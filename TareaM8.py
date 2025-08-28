import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
from io import BytesIO
import sqlite3
import os
from fpdf import FPDF

# Configuración de la página
st.set_page_config(
    page_title="Aplicación de Análisis Deportivo",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funciones de autenticación
def check_password():
    """Retorna True si el usuario ingresa la contraseña correcta."""
    def password_entered():
        """Verifica si el password ingresado es correcto."""
        if st.session_state["username"] == "admin" and st.session_state["password"] == "admin":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # No almacenar password
            del st.session_state["username"]  # No almacenar username
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Primera vez, mostrar inputs
        st.title("🔐 Sistema de Autenticación")
        st.markdown("---")
        st.info("**Usuario:** admin | **Contraseña:** admin")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Usuario", key="username", placeholder="Ingrese su usuario")
            st.text_input("Contraseña", type="password", key="password", placeholder="Ingrese su contraseña")
            st.button("Iniciar Sesión", on_click=password_entered, type="primary")
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrecto, mostrar input nuevamente
        st.title("🔐 Bienvenido a los Datos de Fútbo")
        st.error("Usuario o contraseña incorrectos")
        st.info("**Usuario:** admin | **Contraseña:** admin")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Usuario", key="username", placeholder="Ingrese su usuario")
            st.text_input("Contraseña", type="password", key="password", placeholder="Ingrese su contraseña")
            st.button("Iniciar Sesión", on_click=password_entered, type="primary")
        return False
    else:
        # Password correcto
        return True

# Función para cargar datos CSV
@st.cache_data
def load_csv_data(file_path):
    """Carga datos desde un archivo CSV con cache."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo {file_path}: {str(e)}")
        return pd.DataFrame()

# Función para crear base de datos SQLite (simulando segunda fuente de datos)
@st.cache_resource
def init_database():
    """Inicializa base de datos SQLite con datos de ejemplo."""
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    
    # Crear tabla de equipos
    conn.execute('''
        CREATE TABLE equipos (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            liga TEXT NOT NULL,
            fundacion INTEGER,
            estadio TEXT
        )
    ''')
    
    # Insertar datos de ejemplo
    equipos_data = [
        (1, 'Real Madrid', 'La Liga', 1902, 'Santiago Bernabéu'),
        (2, 'FC Barcelona', 'La Liga', 1899, 'Camp Nou'),
        (3, 'Atlético Madrid', 'La Liga', 1903, 'Cívitas Metropolitano'),
        (4, 'Manchester United', 'Premier League', 1878, 'Old Trafford'),
        (5, 'Liverpool', 'Premier League', 1892, 'Anfield'),
        (6, 'Bayern Munich', 'Bundesliga', 1900, 'Allianz Arena'),
    ]
    
    conn.executemany('INSERT INTO equipos VALUES (?, ?, ?, ?, ?)', equipos_data)
    conn.commit()
    
    return conn

# Función para obtener datos de la base de datos
@st.cache_data
def get_teams_data():
    """Obtiene datos de equipos de la base de datos."""
    conn = init_database()
    df = pd.read_sql_query('SELECT * FROM equipos', conn)
    conn.close()
    return df

# Función para exportar a PDF
class CustomPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 5, '='*95, 0, 1, 'C')
        self.cell(0, 10, 'Análisis Deportivo', 0, 1, 'C')
        self.cell(0, 5, '='*95, 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, '*'*150, 0, 1, 'C')
        fecha = datetime.now().strftime("%d/%m/%Y")
        self.cell(0, 5, f'Reporte generado el {fecha}', 0, 1, 'C')
    
    def set_creation_date(self, headers, data):
        self.set_font('Arial', 'B', 10)
        line_height = 6
        col_width = 45

        margin_left = 15

        self.set_x(margin_left)
        for header in headers:
            header_clean = header.encode('ascii', 'replace').decode()
            self.cell(col_width, line_height, header_clean, 1, 0, 'C')
        self.ln()

        self.set_font('Arial', '', 9)
        for row in data:
            self.set_x(margin_left)
            for item in row:
                item_clean = str(item).encode('ascii', 'replace').decode()
                self.cell(col_width, line_height, item_clean, 1, 0, 'C')
            self.ln()

    def generar_pdf(self, headers, data):
        """Genera el PDF con los datos proporcionados."""
        self.add_page()
        self.set_creation_date(headers, data)
        self.output('reporte.pdf')
        pdf = CustomPDF()

def export_to_pdf(fig, title):
    """Exporta gráfico a PDF."""
    try:
        img_bytes = fig.to_image(format="pdf")
        b64 = base64.b64encode(img_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{title}.pdf">📄 Descargar PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("PDF generado correctamente.")
    except Exception as e:
        st.error(f"Error al exportar PDF: {str(e)}")

# Página 1: Análisis de Datos de Jugadores
def page_players():
    st.title("📊 Análisis de Jugadores")
    st.markdown("---")
    
    # Nota para cargar datos reales
    if not os.path.exists('data/jugadores.csv'):
        st.warning("⚠️ Archivo 'data/jugadores.csv' no encontrado. Mostrando datos de ejemplo.")
        
        # Crear datos de ejemplo para jugadores
        sample_players = {
            'Nombre': ['Lionel Messi', 'Cristiano Ronaldo', 'Kylian Mbappé', 'Erling Haaland', 'Vinicius Jr.'],
            'Equipo': ['PSG', 'Al Nassr', 'PSG', 'Manchester City', 'Real Madrid'],
            'Edad': [36, 39, 25, 23, 23],
            'Goles': [30, 35, 29, 36, 20],
            'Asistencias': [20, 8, 17, 8, 16],
            'Partidos': [34, 32, 36, 35, 32],
            'Valor_Mercado': [35, 15, 180, 150, 100]
        }
        players_df = pd.DataFrame(sample_players)
    else:
        players_df = load_csv_data('data/jugadores.csv')
    
    if not players_df.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🏆 Top Goleadores")
            top_scorers = players_df.nlargest(5, 'Goles')
            
            fig_goals = px.bar(
                top_scorers, 
                x='Nombre', 
                y='Goles',
                color='Goles',
                title='Top 5 Goleadores',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig_goals, use_container_width=True)
            
        with col2:
            st.subheader("📈 Estadísticas Generales")
            total_goals = players_df['Goles'].sum()
            total_assists = players_df['Asistencias'].sum()
            avg_age = players_df['Edad'].mean()
            
            st.metric("Total Goles", total_goals)
            st.metric("Total Asistencias", total_assists)
            st.metric("Edad Promedio", f"{avg_age:.1f}")
        
        # Tabla de datos
        st.subheader("📋 Datos de Jugadores")
        st.dataframe(players_df, use_container_width=True)
        
        # Botones de exportación
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🖨️ Imprimir Página", key="print_players"):
                st.success("Función de impresión activada (Ctrl+P)")
                st.markdown("""
                <script>
                window.print();
                </script>
                """, unsafe_allow_html=True)
        
        with col2:
            if st.button("📄 Exportar Gráfico a PDF", key="pdf_players"):
                export_to_pdf(fig_goals, "top_goleadores")
                st.success("Gráfico exportado a PDF.")

# Página 2: Análisis de Equipos
def page_teams():
    st.title("🏟️ Análisis de Equipos")
    st.markdown("---")
    
    # Cargar datos de equipos desde base de datos (SQLite)
    teams_df = get_teams_data()
    
    # Cargar datos adicionales desde CSV
    if not os.path.exists('data/equipos_stats.csv'):
        st.warning("⚠️ Archivo 'data/equipos_stats.csv' no encontrado. Mostrando datos de ejemplo.")
        
        # Crear datos de ejemplo para estadísticas de equipos
        sample_stats = {
            'Equipo': ['Real Madrid', 'FC Barcelona', 'Atlético Madrid', 'Manchester United', 'Liverpool', 'Bayern Munich'],
            'Partidos_Jugados': [38, 38, 38, 38, 38, 34],
            'Victorias': [28, 24, 22, 20, 24, 26],
            'Empates': [6, 8, 10, 8, 8, 6],
            'Derrotas': [4, 6, 6, 10, 6, 2],
            'Goles_Favor': [89, 76, 65, 72, 84, 92],
            'Goles_Contra': [32, 38, 35, 48, 28, 25]
        }
        stats_df = pd.DataFrame(sample_stats)
    else:
        stats_df = load_csv_data('data/equipos_stats.csv')
    
    # Combinar datos de equipos con estadísticas
    if not stats_df.empty:
        combined_df = pd.merge(teams_df, stats_df, left_on='nombre', right_on='Equipo', how='inner')
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("⚽ Goles a Favor vs Goles en Contra")
            fig_scatter = px.scatter(
                combined_df, 
                x='Goles_Contra', 
                y='Goles_Favor',
                size='Victorias',
                color='liga',
                hover_name='nombre',
                title='Rendimiento Ofensivo vs Defensivo'
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with col2:
            st.subheader("🏆 Liga Distribution")
            liga_counts = teams_df['liga'].value_counts()
            
            fig_pie = px.pie(
                values=liga_counts.values,
                names=liga_counts.index,
                title='Equipos por Liga'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Tabla combinada
        st.subheader("📊 Información Completa de Equipos")
        display_df = combined_df[['nombre', 'liga', 'estadio', 'Partidos_Jugados', 'Victorias', 'Empates', 'Derrotas', 'Goles_Favor', 'Goles_Contra']]
        st.dataframe(display_df, use_container_width=True)
        
        # Botones de exportación
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🖨️ Imprimir Página", key="print_teams"):
                st.success("Función de impresión activada (Ctrl+P)")
        
        with col2:
            if st.button("📄 Exportar Gráfico a PDF", key="pdf_teams"):
                export_to_pdf(fig_scatter, "rendimiento_equipos")
                export_to_pdf(fig_pie, "distribucion_ligas")
                st.success("PDF generado correctamente.")


# Función principal
def main():
    # Sistema de autenticación
    if not check_password():
        return
    
    # Header de la aplicación
    st.sidebar.success("✅ Sesión iniciada correctamente")
    st.sidebar.markdown("---")
    
    # Menú de navegación
    st.sidebar.title("🚀 Navegación")
    page = st.sidebar.selectbox(
        "Selecciona una página:",
        ["📊 Análisis de Jugadores", "🏟️ Análisis de Equipos"]
    )
    
    # Información de sesión
    st.sidebar.markdown("---")
    st.sidebar.info(f"👤 Usuario: admin\n⏰ Sesión: {datetime.now().strftime('%H:%M:%S')}")
    
    # Botón de logout
    if st.sidebar.button("🚪 Cerrar Sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Renderizar página seleccionada
    if page == "📊 Análisis de Jugadores":
        page_players()
    elif page == "🏟️ Análisis de Equipos":
        page_teams()

if __name__ == "__main__":
    main()