import streamlit as st
from functions import return_entities  # Certifique-se de que esta função está corretamente importada
import streamlit_shadcn_ui as ui
import random
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle
import requests
from bs4 import BeautifulSoup  # Certifique-se de ter o BeautifulSoup instalado

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
    'Teste Scrape',
    'Cálculo de Hardware',  # Nova tela adicionada
], default_value='Visão Geral', key="navigation")

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


elif navPage == 'Teste Scrape':
    st.title("Teste o seu Scrape antes de montar no HomeAssistant/Node-Red")

    st.markdown("""
    ### Instruções:
    - **URL**: Insira a URL completa da página da web que deseja fazer o scraping.
    - **Seletor CSS**: Forneça o seletor CSS do elemento que deseja extrair. Pode ser um ID, classe ou qualquer seletor válido.
    - **Exemplo de Seletor**: Para selecionar um elemento com ID "preço", use `#preco`. Para uma classe "titulo", use `.titulo`.
    - **Atenção**: Certifique-se de que a URL é acessível e que o seletor corresponde a um ou mais elementos na página.
    """)

    # Formulário de entrada
    with st.form(key='scrape_form'):
        url = st.text_input('URL', value='', help='Insira a URL da página que deseja extrair.')
        selector = st.text_input('Seletor CSS', value='', help='Insira o seletor CSS do elemento.')
        submit_scrape = st.form_submit_button('Enviar')

    if submit_scrape:
        if url and selector:
            try:
                # Realiza a requisição HTTP
                response = requests.get(url)
                response.raise_for_status()  # Verifica se a requisição foi bem-sucedida

                # Analisa o conteúdo HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # Seleciona os elementos com base no seletor CSS
                elements = soup.select(selector)

                if elements:
                    st.success(f'Foram encontrados {len(elements)} elemento(s) com o seletor "{selector}".')
                    # Exibe os elementos encontrados
                    for idx, element in enumerate(elements, start=1):
                        st.markdown(f"#### Resultado {idx}:")
                        st.code(element.get_text(strip=True), language='html')
                else:
                    st.warning(f'Nenhum elemento encontrado com o seletor "{selector}".')
            except requests.exceptions.RequestException as e:
                st.error(f"Erro ao acessar a URL: {e}")
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")
        else:
            st.warning('Por favor, preencha tanto a URL quanto o Seletor CSS.')

        # Dicas para conversão de texto para numérico
        st.markdown("### Dicas para Converter o Retorno em Valor Numérico")

        st.markdown("""
        Se o resultado for um valor como **"R$ 7.379,91"**, você pode precisar converter esse texto em um número para uso em cálculos.
        """)

        st.markdown("#### Em Jinja2 (Home Assistant):")
        st.markdown("""
        - Criar um ajudante pegando deste sensor.
        ```jinja2
        {% set texto = "R$ 7.379,91" %}
        {% set valor = texto | replace("R$ ", "") | replace(".", "") | replace(",", ".") | trim | float %}
        """)

        st.markdown("#### Em Node-Red:") 
        st.markdown("""
        Em um nó Function, realizar o tratamento.
        ```
        msg.payload = parseFloat(msg.payload.replace("R$", "").replace(/\./g, "").replace(",", ".").trim());
        """)

        
elif navPage == 'Cálculo de Hardware':
    st.title("Cálculo de Hardware Necessário para o Home Assistant")

    st.markdown("""
    ### Instruções:
    - Selecione a quantidade de dispositivos que você pretende utilizar no Home Assistant.
    - Com base nos dispositivos selecionados, o sistema calculará o hardware mínimo recomendado.
    """)

    # Formulário de entrada
    with st.form(key='hardware_form'):
        st.markdown("#### Dispositivos Básicos")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            num_luzes = st.number_input('Número de Luzes', min_value=0, value=0, step=1)
        with col2:
            num_tomadas = st.number_input('Número de Tomadas Inteligentes', min_value=0, value=0, step=1)
        with col3:
            num_sensores_abertura = st.number_input('Número de Sensores de Abertura', min_value=0, value=0, step=1)
        with col4:
            num_sensores_movimento = st.number_input('Número de Sensores de Movimento', min_value=0, value=0, step=1)

        st.markdown("#### Dispositivos de Alta Demanda")
        col3, col4 = st.columns(2)
        with col3:
            num_cameras = st.number_input('Número de Câmeras', min_value=0, value=0, step=1)
            num_dispositivos_streaming = st.number_input('Número de Dispositivos de Streaming (Chromecast, etc.)', min_value=0, value=0, step=1)

        st.markdown("#### Integrações Adicionais")
        col5, col6 = st.columns(2)
        with col5:
            usar_assistente_virtual = st.checkbox('Utilizar Assistente Virtual (Alexa, Google Assistant)')
            usar_automacoes_complexas = st.checkbox('Utilizar Automações Complexas')
            usar_frigate = st.checkbox('Utilizar o Frigate (Add-on para detecção de câmeras)')
        with col6:
            usar_addons = st.checkbox('Utilizar Add-ons Pesados (ex: Node-Red, InfluxDB)')

        submit_hardware = st.form_submit_button('Calcular Hardware')

    if submit_hardware:
        # Cálculo do hardware necessário
        # Definir valores base
        cpu_base = 1  # 1 núcleo
        ram_base = 1  # 1 GB
        storage_base = 16  # 16 GB

        # Ajustes com base nos dispositivos básicos
        dispositivos_basicos = num_luzes + num_tomadas + num_sensores_abertura + num_sensores_movimento
        cpu_base += dispositivos_basicos * 0.05  # Cada dispositivo básico adiciona 0.05 núcleos
        ram_base += dispositivos_basicos * 0.02  # Cada dispositivo básico adiciona 20 MB de RAM

        # Ajustes com base em dispositivos de alta demanda
        cpu_base += num_cameras * 0.5  # Cada câmera adiciona 0.5 núcleos
        ram_base += num_cameras * 0.5  # Cada câmera adiciona 500 MB de RAM

        cpu_base += num_dispositivos_streaming * 0.1
        ram_base += num_dispositivos_streaming * 0.05

        # Ajustes com base em integrações adicionais
        if usar_assistente_virtual:
            cpu_base += 0.2
            ram_base += 0.1

        if usar_automacoes_complexas:
            cpu_base += 0.3
            ram_base += 0.2

        if usar_addons:
            cpu_base += 0.5
            ram_base += 0.5
            storage_base += 8  # Add-ons pesados requerem mais espaço em disco

        # Ajustes específicos para o Frigate
        if usar_frigate:
            cpu_base += num_cameras * 1.0  # Frigate adiciona 1 núcleo por câmera
            ram_base += num_cameras * 0.5  # Frigate adiciona 500 MB de RAM por câmera
            storage_base += num_cameras * 10  # Frigate requer armazenamento extra por câmera (10 GB)

        # Arredondar valores
        cpu_recomendado = round(cpu_base, 1)
        ram_recomendado = round(ram_base, 1)
        storage_recomendado = round(storage_base)

        # Exibir resultados
        st.markdown("### Hardware Recomendado:")
        st.markdown(f"- **CPU**: {cpu_recomendado} núcleo(s)")
        st.markdown(f"- **Memória RAM**: {ram_recomendado} GB")
        st.markdown(f"- **Armazenamento**: {storage_recomendado} GB")

        # Sugestões de hardware com base nos resultados
        st.markdown("### Sugestões de Hardware:")

        if cpu_recomendado <= 2 and ram_recomendado <= 2:
            st.markdown("- Um **Raspberry Pi 4** com 2GB de RAM pode ser suficiente.")
            st.markdown("- **Processador**: Broadcom BCM2711, Quad core Cortex-A72 (ARM v8) 64-bit SoC @ 1.5GHz")
        elif cpu_recomendado <= 4 and ram_recomendado <= 4:
            st.markdown("- Considere um **Raspberry Pi 4** com 4GB de RAM ou um **mini PC**.")
            st.markdown("- **Processadores sugeridos**: Intel Celeron J4105, Intel Pentium Silver N5000")
        else:
            st.markdown("- É recomendado um **PC dedicado** ou um **servidor NAS** com recursos mais robustos.")
            st.markdown("- **Processadores sugeridos**: Intel Core i3/i5/i7 de última geração, AMD Ryzen 3/5/7")

        st.markdown("#### Observações:")
        st.markdown("- Estes são valores estimados. Dependendo das especificidades dos dispositivos e integrações, os requisitos podem variar.")
        st.markdown("- Para uso com câmeras e add-ons pesados como o Frigate, é altamente recomendado usar um hardware mais robusto.")


    else:
        st.warning('Por favor, insira a URL Externa e o Token na barra lateral e clique em Enviar.')

