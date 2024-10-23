import streamlit as st
from functions import return_entities  # Certifique-se de que esta função está corretamente importada
import streamlit_shadcn_ui as ui
import random
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle

# Configurações
st.set_page_config(layout="wide", page_title='Smart Chosk - Ferramentas do HomeAssistant', initial_sidebar_state='collapsed')

# Inicializa o estado da sessão
if 'dfEntidades' not in st.session_state:
    st.session_state['dfEntidades'] = None

# Seção de entrada na barra lateral
st.sidebar.header('Configuração')
extUrl = st.sidebar.text_input('URL Externa', value='', placeholder="https://suaurl.nom.br")
token = st.sidebar.text_input('Token', value='', type='password', placeholder="ey.... ( sem o Bearer )")
submitButton = st.sidebar.button("Enviar")

if submitButton:
    dfEntidades = return_entities(extUrl, token)
    st.session_state['dfEntidades'] = dfEntidades

# Navegação por Abas
navPage = ui.tabs(options=[
    'Início',
    'Visão Geral',
    'Visão de Teia',
    'Tabela de Entidades',
], default_value='Início', key="navigation")

if navPage == 'Início':
    st.title("Bem-vindo ao Smart Chosk - Ferramentas do HomeAssistant")

    # Container para avisos
    with st.container():
        st.markdown("""
        ### Avisos Importantes:

        - **Privacidade**: Esta aplicação **não coleta nenhum dado** pessoal ou informações sensíveis.
        - **Propósito**: Destinada apenas para **fins demonstrativos**, refletindo as entidades do seu Home Assistant.
        """)

    # Espaçamento
    st.markdown("---")

    # Container para o QR Code de doação
    with st.container():
        st.markdown("### Apoie o Projeto")
        st.markdown("Ajude a manter este projeto ativo fazendo uma doação via PIX utilizando o QR Code abaixo:")
        st.image('imagem_qr_code.jpg', caption='Faça uma doação via PIX', width=400)

elif navPage == 'Visão Geral':
    st.header('Visão Geral')

    # Após buscar dfEntidades
    if st.session_state['dfEntidades' ] is not None:
        dfEntidades = st.session_state['dfEntidades']

        # Total de Entidades
        totalEntidades = int(len(dfEntidades))

        # Total de Entidades Indisponíveis e Desconhecidas
        totalEntidadesUnav = int(dfEntidades['state'].value_counts().get('unavailable', 0))
        totalEntidadesUnknown = int(dfEntidades['state'].value_counts().get('unknown', 0))

        # Extrai o tipo de dispositivo do entity_id
        dfEntidades['device_type'] = dfEntidades['entity_id'].str.split('.').str[0]

        # Contagem do número de cada device_type
        device_type_counts = dfEntidades['device_type'].value_counts()

        # Obtém quantidades de tipos de dispositivos específicos
        specific_device_types = ['light', 'sensor', 'switch', 'binary_sensor']
        device_counts = {device_type: int(device_type_counts.get(device_type, 0)) for device_type in specific_device_types}

        # Cálculos para percentuais
        percent_lights = (device_counts['light'] / totalEntidades) * 100 if totalEntidades > 0 else 0
        percent_unavailable = (totalEntidadesUnav / totalEntidades) * 100 if totalEntidades > 0 else 0

        # Container de Cards no topo
        cardsContainer = st.container()
        with cardsContainer:
            cols = st.columns(7)
            card_titles = ["Entidades 📦", "Indisponíveis ⚠️", "Desconhecidas ❓", "Luzes 💡", "Sensores 📟", "Interruptores 🔌", "Sensores Binários 🖳"]
            card_values = [totalEntidades, totalEntidadesUnav, totalEntidadesUnknown,
                        device_counts['light'], device_counts['sensor'],
                        device_counts['switch'], device_counts['binary_sensor']]
            for col, title, value in zip(cols, card_titles, card_values):
                with col:
                    ui.metric_card(title=title, content=value, key=f"card_{title}")

        # Mensagens abaixo dos cards
        st.markdown(f"### Seu Home Assistant tem **{totalEntidades}** entidades")
        st.markdown(f"💡 As luzes representam **{percent_lights:.2f}%** das entidades totais")
        st.markdown(f"⚠️ As entidades indisponíveis são **{percent_unavailable:.2f}%** do total")

        # Análises adicionais
        # Top 5 tipos de entidades por contagem com percentuais
        device_type_percentages = (device_type_counts / totalEntidades * 100).round(2)
        top_entity_types = device_type_counts.head(5).reset_index()
        top_entity_types['Porcentagem (%)'] = device_type_percentages.head(5).values

        st.markdown("#### Os 5 tipos de entidades mais comuns são:")
        st.table(top_entity_types.rename(columns={
            'index': 'Tipo de Entidade',
            'device_type': 'Contagem'
        }))

        # Análise de entidades indisponíveis
        df_unavailable = dfEntidades[dfEntidades['state'] == 'unavailable']
        if not df_unavailable.empty:
            unavailable_counts = df_unavailable['device_type'].value_counts()

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Tipos de entidades mais indisponíveis:")
                st.table(unavailable_counts.reset_index().rename(columns={
                    'index': 'Tipo de Entidade',
                    'device_type': 'Contagem'
                }))

            with col2:
                # Filtro por tipo de dispositivo
                unavailable_device_types = df_unavailable['device_type'].unique()
                selected_device_type = st.selectbox('Filtrar por tipo de dispositivo', options=unavailable_device_types)

                # Filtra os dispositivos indisponíveis
                df_unavailable_filtered = df_unavailable[df_unavailable['device_type'] == selected_device_type]
                # Exibe a tabela de dispositivos indisponíveis
                st.markdown(f"#### Dispositivos indisponíveis do tipo **{selected_device_type}**:")
                st.table(df_unavailable_filtered[['entity_id', 'state']].rename(columns={
                    'entity_id': 'ID da Entidade',
                    'state': 'Estado'
                }))
        else:
            st.info("Não há dispositivos indisponíveis no momento.")

    else:
        st.warning('Por favor, insira a URL Externa e o Token na barra lateral e clique em Enviar.')

elif navPage == 'Visão de Teia':
    st.header('Visão de Teia por Tipo de Entidade')

    if st.session_state['dfEntidades'] is not None:
        dfEntidades = st.session_state['dfEntidades']

        # Extrai o tipo de dispositivo do entity_id
        dfEntidades['device_type'] = dfEntidades['entity_id'].str.split('.').str[0]

        # Obtém tipos únicos de entidades
        unique_types = dfEntidades['device_type'].unique()

        # Multiselect para tipos de entidades
        selected_types = st.multiselect('Selecione os tipos de entidades para incluir', options=unique_types, default=unique_types)

        # Filtra o dataframe
        df_filtered = dfEntidades[dfEntidades['device_type'].isin(selected_types)]

        # Limita o número de dispositivos se necessário
        df_dispositivos = df_filtered.head(100)

        # Prepara nós e arestas
        elements = {
            "nodes": [],
            "edges": []
        }

        # Lista de estilos de nós
        node_styles = []

        # Define cores para cada tipo
        type_colors = {tipo: "#%06x" % random.randint(0, 0xFFFFFF) for tipo in selected_types}

        # Adiciona nós de tipo e seus estilos
        for tipo in selected_types:
            tipo_node_id = f"{tipo}_node"
            elements["nodes"].append({
                "data": {
                    "id": tipo_node_id,
                    "label": tipo.upper(),
                    "icon": "home"
                }
            })
            # Adiciona estilo do nó de tipo
            node_styles.append(
                NodeStyle(f"{tipo_node_id}", type_colors[tipo], "label", tipo)
            )

        # Adiciona nós de detalhes e arestas, e seus estilos
        for idx, row in df_dispositivos.iterrows():
            entity_id = row['entity_id']
            device_type = row['device_type']
            state = row['state']
            tipo_node_id = f"{device_type}_node"

            # Determina a cor do nó com base no estado
            node_color = "#FF0000" if state in ['unavailable', 'unknown'] else "#00FF00"

            elements["nodes"].append({
                "data": {
                    "id": entity_id,
                    "label": entity_id,
                    "type": device_type
                }
            })

            # Cria uma aresta entre o nó de tipo e o nó de detalhe
            elements["edges"].append({
                "data": {
                    "id": f"{tipo_node_id}_{entity_id}",
                    "label": f"{device_type.upper()}_LINK",
                    "source": tipo_node_id,
                    "target": entity_id
                }
            })

            # Armazena o estilo do nó
            node_styles.append(
                NodeStyle(
                    entity_id,
                    node_color,
                    "label",
                    device_type
                )
            )

        # Estilos de arestas
        edge_labels = set([edge['data']['label'] for edge in elements['edges']])
        edge_styles = [
            EdgeStyle(edge_label, labeled=True, directed=False)
            for edge_label in edge_labels
        ]

        # Renderiza o gráfico
        st.markdown("### Visualização de Nós por Tipo de Entidade")
        st_link_analysis(
            elements=elements,
            layout="cose",
            node_styles=node_styles,
            edge_styles=edge_styles,
        )

    else:
        st.warning('Por favor, insira a URL Externa e o Token na barra lateral e clique em Enviar.')

elif navPage == 'Tabela de Entidades':
    st.title("Tabela de Entidades")
    if st.session_state['dfEntidades'] is not None:
        dfEntidades = st.session_state['dfEntidades']
        st.dataframe(dfEntidades, hide_index=True, use_container_width=True)
    else:
        st.warning('Por favor, insira a URL Externa e o Token na barra lateral e clique em Enviar.')
