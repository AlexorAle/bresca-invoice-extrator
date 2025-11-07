"""
Dashboard de Streamlit para visualización de facturas
"""
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
from pathlib import Path
import os
import sys
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parents[1]))

from db.database import get_database
from db.repositories import FacturaRepository
from security.secrets import load_env

# Cargar variables de entorno
load_env()

# Configuración de página
st.set_page_config(
    page_title="Dashboard de Facturas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar configuración de autenticación
config_path = Path(__file__).parent / 'config.yaml'

if not config_path.exists():
    st.error(f"⚠️ Archivo config.yaml no encontrado en {config_path}")
    st.info("Por favor, ejecuta `python scripts/generate_config.py` para crear el archivo de configuración")
    st.stop()

with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

# Inicializar autenticador
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Login
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('❌ Usuario o contraseña incorrectos')
    st.stop()

elif authentication_status == None:
    st.warning('👋 Por favor, ingresa tus credenciales')
    st.stop()

elif authentication_status:
    # Usuario autenticado
    
    # Sidebar con logout y filtros
    with st.sidebar:
        st.write(f'Bienvenido/a, **{name}**')
        authenticator.logout('Cerrar Sesión', 'sidebar')
        
        st.markdown("---")
        st.header("Filtros")
        
        # Inicializar base de datos
        @st.cache_resource
        def init_db():
            return get_database()
        
        db = init_db()
        repo = FacturaRepository(db)
        
        # Filtros
        filter_month = st.selectbox(
            "Mes",
            options=["Todos", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        )
        
        filter_estado = st.multiselect(
            "Estado",
            options=["procesado", "pendiente", "error", "revisar"],
            default=["procesado"]
        )
        
        filter_confianza = st.multiselect(
            "Confianza",
            options=["alta", "media", "baja"],
            default=["alta", "media", "baja"]
        )
        
        st.markdown("---")
        
        # Botón de actualizar
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Main content
    st.title("📊 Dashboard de Facturas")
    st.markdown("---")
    
    # Cargar datos
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def load_facturas():
        facturas = repo.get_all_facturas(limit=1000)
        if not facturas:
            return pd.DataFrame()
        return pd.DataFrame(facturas)
    
    @st.cache_data(ttl=300)
    def load_stats():
        return repo.get_statistics()
    
    df = load_facturas()
    stats = load_stats()
    
    if df.empty:
        st.warning("⚠️ No hay facturas en la base de datos")
        st.info("Ejecuta `python src/main.py` para procesar facturas")
        st.stop()
    
    # Convertir fecha_emision a datetime
    if 'fecha_emision' in df.columns:
        df['fecha_emision'] = pd.to_datetime(df['fecha_emision'], errors='coerce')
        df['mes'] = df['fecha_emision'].dt.month_name(locale='es_ES.UTF-8').fillna('Desconocido')
        df['año'] = df['fecha_emision'].dt.year
    
    # Aplicar filtros
    df_filtered = df.copy()
    
    if filter_month != "Todos":
        df_filtered = df_filtered[df_filtered['mes'].str.lower() == filter_month.lower()]
    
    if filter_estado:
        df_filtered = df_filtered[df_filtered['estado'].isin(filter_estado)]
    
    if filter_confianza:
        df_filtered = df_filtered[df_filtered['confianza'].isin(filter_confianza)]
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Facturas",
            value=f"{len(df_filtered):,}",
            delta=f"{len(df_filtered) - stats['total_facturas']} filtradas" if len(df_filtered) != stats['total_facturas'] else None
        )
    
    with col2:
        total_importe = df_filtered['importe_total'].sum()
        st.metric(
            label="Importe Total",
            value=f"€{total_importe:,.2f}"
        )
    
    with col3:
        promedio = df_filtered['importe_total'].mean() if len(df_filtered) > 0 else 0
        st.metric(
            label="Importe Promedio",
            value=f"€{promedio:,.2f}"
        )
    
    with col4:
        confianza_alta = len(df_filtered[df_filtered['confianza'] == 'alta'])
        porcentaje = (confianza_alta / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        st.metric(
            label="Confianza Alta",
            value=f"{confianza_alta}",
            delta=f"{porcentaje:.1f}%"
        )
    
    st.markdown("---")
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Tabla", "📈 Gráficos", "⚠️ Errores", "📤 Exportar"])
    
    with tab1:
        st.subheader("Listado de Facturas")
        
        # Configurar columnas a mostrar
        columns_to_show = [
            'drive_file_name', 'proveedor_text', 'fecha_emision',
            'importe_total', 'confianza', 'estado', 'extractor'
        ]
        
        # Mostrar tabla
        st.dataframe(
            df_filtered[columns_to_show],
            use_container_width=True,
            hide_index=True,
            column_config={
                'drive_file_name': st.column_config.TextColumn('Archivo', width='medium'),
                'proveedor_text': st.column_config.TextColumn('Proveedor', width='medium'),
                'fecha_emision': st.column_config.DateColumn('Fecha Emisión', format='DD/MM/YYYY'),
                'importe_total': st.column_config.NumberColumn('Importe', format='€%.2f'),
                'confianza': st.column_config.TextColumn('Confianza', width='small'),
                'estado': st.column_config.TextColumn('Estado', width='small'),
                'extractor': st.column_config.TextColumn('Extractor', width='small')
            }
        )
    
    with tab2:
        st.subheader("Visualizaciones")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de facturas por mes
            st.markdown("##### Facturas por Mes")
            if 'mes' in df_filtered.columns:
                facturas_por_mes = df_filtered.groupby('mes').size().reset_index(name='cantidad')
                
                fig = px.bar(
                    facturas_por_mes,
                    x='mes',
                    y='cantidad',
                    title='',
                    labels={'mes': 'Mes', 'cantidad': 'Cantidad de Facturas'},
                    color='cantidad',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico de distribución por proveedor (top 10)
            st.markdown("##### Top 10 Proveedores")
            proveedores = df_filtered[df_filtered['proveedor_text'].notna()].groupby(
                'proveedor_text'
            ).size().reset_index(name='cantidad').sort_values('cantidad', ascending=False).head(10)
            
            if not proveedores.empty:
                fig = px.pie(
                    proveedores,
                    values='cantidad',
                    names='proveedor_text',
                    title=''
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de importes por mes
        st.markdown("##### Importes por Mes")
        if 'mes' in df_filtered.columns:
            importes_por_mes = df_filtered.groupby('mes')['importe_total'].sum().reset_index()
            
            fig = px.line(
                importes_por_mes,
                x='mes',
                y='importe_total',
                title='',
                labels={'mes': 'Mes', 'importe_total': 'Importe Total (€)'},
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Distribución por confianza y extractor
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Distribución por Confianza")
            confianza_dist = df_filtered.groupby('confianza').size().reset_index(name='cantidad')
            
            fig = px.bar(
                confianza_dist,
                x='confianza',
                y='cantidad',
                color='confianza',
                color_discrete_map={'alta': '#28a745', 'media': '#ffc107', 'baja': '#dc3545'},
                labels={'confianza': 'Confianza', 'cantidad': 'Cantidad'}
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### Distribución por Extractor")
            extractor_dist = df_filtered.groupby('extractor').size().reset_index(name='cantidad')
            
            fig = px.bar(
                extractor_dist,
                x='extractor',
                y='cantidad',
                color='extractor',
                labels={'extractor': 'Extractor', 'cantidad': 'Cantidad'}
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Facturas con Errores o para Revisar")
        
        # Filtrar facturas con problemas
        df_errores = df[
            (df['estado'].isin(['error', 'revisar'])) |
            (df['confianza'] == 'baja')
        ]
        
        if df_errores.empty:
            st.success("✅ No hay facturas con errores o que requieran revisión")
        else:
            st.warning(f"⚠️ {len(df_errores)} facturas requieren atención")
            
            # Mostrar detalles
            for idx, row in df_errores.iterrows():
                with st.expander(f"📄 {row['drive_file_name']} - Estado: {row['estado']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Proveedor:** {row.get('proveedor_text', 'N/A')}")
                        st.write(f"**Número:** {row.get('numero_factura', 'N/A')}")
                        st.write(f"**Fecha:** {row.get('fecha_emision', 'N/A')}")
                        st.write(f"**Importe:** €{row.get('importe_total', 0):.2f}")
                    
                    with col2:
                        st.write(f"**Estado:** {row['estado']}")
                        st.write(f"**Confianza:** {row['confianza']}")
                        st.write(f"**Extractor:** {row['extractor']}")
                        if row.get('error_msg'):
                            st.error(f"**Error:** {row['error_msg']}")
    
    with tab4:
        st.subheader("Exportar Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Exportar a CSV")
            
            # Preparar CSV
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"facturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            st.markdown("##### Exportar a Excel")
            
            # Preparar Excel (requiere openpyxl)
            try:
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtered.to_excel(writer, index=False, sheet_name='Facturas')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar Excel",
                    data=excel_data,
                    file_name=f"facturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except ImportError:
                st.warning("⚠️ Instala openpyxl para exportar a Excel: `pip install openpyxl`")
        
        st.markdown("---")
        st.markdown("##### Resumen de Exportación")
        st.info(f"""
        📊 **Facturas a exportar:** {len(df_filtered)}  
        💰 **Importe total:** €{df_filtered['importe_total'].sum():,.2f}  
        📅 **Rango de fechas:** {df_filtered['fecha_emision'].min()} - {df_filtered['fecha_emision'].max()}
        """)
    
    # Footer
    st.markdown("---")
    st.caption(f"Dashboard de Facturas v1.0 | Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
