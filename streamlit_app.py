import streamlit as st
from functions import return_entities  # Certifique-se de que esta função está corretamente importada
import streamlit_shadcn_ui as ui
import random
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle
import requests
from bs4 import BeautifulSoup  # Certifique-se de ter o BeautifulSoup instalado
from collections import OrderedDict
import yaml  # Biblioteca para trabalhar com YAML
import base64


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
    'Cálculo de Hardware (Beta)',
    'Assistente de Configuração do Frigate',  # Nova página adicionada
    'Floorplan Helper'
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

        
elif navPage == 'Cálculo de Hardware (Beta)':
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
            num_cameras = st.number_input('Número de Câmeras (Máximo recomendado: 20)', min_value=0, value=0, step=1)
            num_dispositivos_streaming = st.number_input('Número de Dispositivos de Streaming (Chromecast, etc.)', min_value=0, value=0, step=1)

        usar_cpu = False
        usar_openvino = False

        st.markdown("#### Integrações Adicionais")
        col5, col6 = st.columns(2)
        with col5:
            usar_assistente_virtual = st.checkbox('Utilizar Assistente Virtual (Alexa, Google Assistant)')
            usar_automacoes_complexas = st.checkbox('Utilizar Automações Complexas')
            usar_frigate = st.checkbox('Utilizar o Frigate (Add-on para detecção de câmeras)')
            if usar_frigate:
                st.write("#### Unidade de Processamento de IA (Frigate)")
                usar_cpu = st.checkbox('Utilizar CPU (Não recomendado)', value=True)
                usar_coral = st.checkbox('Utilizar Google Coral')
                usar_openvino = st.checkbox('Utilizar Openvino (O processador deve suportar instruções AVX2)')
        with col6:
            usar_addons = st.checkbox('Utilizar Add-ons Pesados (ex: Node-Red, InfluxDB)')

        submit_hardware = st.form_submit_button('Calcular Hardware')

    if submit_hardware:
        # Cálculo do hardware necessário
        # Definir valores base
        cpu_base = 4.0  # 4 núcleo
        ram_base = 4.0  # 4 GB
        storage_base = 16  # 16 GB

        def arredondar_para_par(numero):
            return int(round(numero / 2) * 2)

        # Ajustes com base nos dispositivos básicos
        dispositivos_basicos = num_luzes + num_tomadas + num_sensores_abertura + num_sensores_movimento
        ram_base += (dispositivos_basicos // 50) * 0.5  # A cada 50 dispositivos básicos, adiciona 0.5GB de RAM
        
        # Ajustes com base em dispositivos de alta demanda
        cpu_base += (num_cameras // 5) * 0.5 # Cada 5 câmeras adiciona 0.5 núcleos
        ram_base += (num_cameras // 5) * 0.5 # Cada 5 câmeras adiciona 500 MB de RAM
        storage_base += num_cameras // 5 # Cada 5 câmeras adiciona 1 GB de armazenamento
    #    cpu_base += num_cameras * 0.2  # Cada câmera adiciona 0.5 núcleos
    #    ram_base += num_cameras * 0.1  # Cada câmera adiciona 500 MB de RAM

        cpu_base += num_dispositivos_streaming * 0.1
        ram_base += num_dispositivos_streaming * 0.05

        # Ajustes com base em integrações adicionais
        if usar_assistente_virtual:
        #    cpu_base += 0.2
            ram_base += 0.1

        if usar_automacoes_complexas:
            cpu_base += 0.2
            ram_base += 0.2

        if usar_addons:
        #    cpu_base += 0.5
            ram_base += 0.5
            storage_base += 8  # Add-ons pesados requerem mais espaço em disco

        if usar_frigate:
            if usar_coral or usar_openvino:
                cpu_base += num_cameras * (0.1 if usar_coral else 0.3)
            else:
                cpu_base += num_cameras * 0.8
            ram_base += num_cameras * 0.7  # 500 MB de RAM por câmera
            storage_base += num_cameras * 65  # 65GB de armazenamento por câmera para 1 dia de gravação contínua

        # Limitar o número de núcleos a 96
        max_cores = 96
        cpu_base = min(cpu_base, max_cores)

        # Arredondar valores
        cpu_recomendado = arredondar_para_par(cpu_base)
        ram_recomendado = arredondar_para_par(ram_base)
        storage_recomendado = round(storage_base)

        # Exibir resultados
        st.markdown("### Hardware Mínimo Recomendado:")
        st.markdown(f"- **CPU**: {cpu_recomendado} núcleo(s)")
        st.markdown(f"- **Memória RAM**: {ram_recomendado} GB")
        st.markdown(f"- **Armazenamento**: {storage_recomendado} GB")

        # Sugestões de hardware com base nos resultados
        st.markdown("### Sugestões de Hardware:")

        if cpu_recomendado <= 4 and ram_recomendado <= 4 and not usar_frigate :
            st.markdown("- Um **Raspberry Pi 4** com 4GB de RAM pode ser suficiente.")
            st.markdown("- **Processador**: Broadcom BCM2711, Quad core Cortex-A72 (ARM v8) 64-bit SoC @ 1.5GHz")
        elif cpu_recomendado <= 4 and ram_recomendado <= 8 and not usar_cpu:
            st.markdown("- Considere um **mini PC** com 8GB de RAM.")
            st.markdown("- **Processadores sugeridos** (com suporte ao OpenVINO): Intel N97, Intel N100, Intel N200")
        elif cpu_recomendado <= 8 and ram_recomendado <= 16:
            if not usar_openvino:
                st.markdown("- Um **mini PC** mais potente ou um **servidor NAS** com melhor desempenho.")
                st.markdown("- **Processadores sugeridos**: Intel Core i3/i5 ou AMD Ryzen 3/5\n\n")
            if usar_openvino:
                ("- Um **mini PC** mais potente ou um **servidor NAS** com melhor desempenho.")
                st.markdown("- **Processadores sugeridos**: Intel Core i3/i5\n\n")
                st.markdown("**Nota**: OpenVINO é compatível com processadores Intel de 6ª geração ou superior que suportem instruções AVX2.")        
        elif cpu_recomendado <= 16 and ram_recomendado <= 32:            
            if not usar_openvino:
                st.markdown("- Um **PC dedicado** ou **servidor** de alto desempenho.")
                st.markdown("- **Processadores sugeridos**: Intel Core i7/i9, AMD Ryzen 7/9, Intel Xeon E-series")
            if usar_openvino:
                st.markdown("- Um **PC dedicado** ou **servidor** de alto desempenho.")
                st.markdown("- **Processadores sugeridos**: Intel Core i7/i9")
                st.markdown("**Nota**: OpenVINO é compatível com processadores Intel de 6ª geração ou superior que suportem instruções AVX2.")
        else:
            st.markdown("- **Atenção**: Os requisitos calculados excedem os processadores comuns.")
            st.markdown("- Considere distribuir a carga em múltiplas máquinas ou utilizar hardware de nível servidor.")
            st.markdown("- **Processadores sugeridos**: Múltiplos processadores Intel Xeon ou AMD EPYC")

        st.markdown("#### Observações:")
        st.markdown(f"- **Limite de CPU**: O número máximo recomendado de núcleos é {max_cores}. Para necessidades além disso, recomenda-se considerar soluções especializadas.")
        st.markdown("- **Estimativas Aproximadas**: Os valores apresentados são estimativas. Dependendo das especificidades dos dispositivos e integrações, os requisitos reais podem variar.")
        st.markdown("- **Uso com Câmeras e Add-ons Intensivos**: Para câmeras e add-ons pesados como o Frigate, é recomendado optar por um hardware mais robusto para garantir uma performance consistente.")
        if usar_frigate:
            st.markdown("- **Câmeras de Baixa Resolução e Taxa de Quadros Reduzida**: Câmeras com resolução de até 720p e taxa de quadros de 5 FPS tendem a consumir menos recursos de CPU. Se sua câmera for de alta resolução, como 4K, considere configurar o Frigate para utilizar a transmissão secundária (substream) em vez da transmissão principal, o que pode reduzir significativamente a carga de processamento.")

elif navPage == 'Assistente de Configuração do Frigate':
    st.title("Assistente de Configuração do Frigate")

    st.markdown("""
    ### Instruções:
    - Preencha as configurações gerais do Frigate, como informações do MQTT.
    - Adicione as câmeras que deseja configurar, preenchendo os detalhes de cada uma.
    - Ao final, será gerado o conteúdo do arquivo `frigate.yml` com base nas informações fornecidas.
    """)

    # Lista de objetos disponíveis para rastreamento
    available_objects = [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
        "boat", "traffic light", "fire hydrant", "street sign", "stop sign",
        "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
        "elephant", "bear", "zebra", "giraffe", "hat", "backpack", "umbrella",
        "shoe", "eye glasses", "handbag", "tie", "suitcase", "frisbee", "skis",
        "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
        "skateboard", "surfboard", "tennis racket", "bottle", "plate", "wine glass",
        "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich",
        "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
        "chair", "couch", "potted plant", "bed", "mirror", "dining table",
        "window", "desk", "toilet", "door", "tv", "laptop", "mouse", "remote",
        "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
        "refrigerator", "blender", "book", "clock", "vase", "scissors",
        "teddy bear", "hair drier", "toothbrush", "hair brush"
    ]

    # Formulário de entrada
    with st.form(key='frigate_form'):
        st.markdown("#### Configurações Gerais")
        col_mqtt1, col_mqtt2, col_mqtt3 = st.columns(3)
        with col_mqtt1:
            mqtt_host = st.text_input('Host MQTT', value='', help='Endereço IP ou hostname do broker MQTT.')
        with col_mqtt2:
            mqtt_user = st.text_input('Usuário MQTT', value='', help='Usuário para autenticação no MQTT.')
        with col_mqtt3:
            mqtt_password = st.text_input('Senha MQTT', value='', type='password', help='Senha para autenticação no MQTT.')

        st.markdown("#### Configurações das Câmeras")

        camera_list = []

        num_cameras = st.number_input('Número de Câmeras', min_value=1, value=1, step=1, help='Quantas câmeras você deseja configurar?')

        for i in range(int(num_cameras)):
            st.markdown(f"##### Configuração da Câmera {i+1}")
            camera_name = st.text_input(f'Nome da Câmera {i+1}', value=f'camera_{i+1}', key=f'camera_name_{i}')
            camera_path = st.text_input(f'URL RTSP da Câmera {i+1}', value='', key=f'camera_path_{i}', help='Exemplo: rtsp://usuario:senha@ip_da_camera:554/...')
            
            col_cam1, col_cam2, col_cam3 = st.columns(3)
            with col_cam1:
                detect_width = st.number_input(f'Largura de Detecção', min_value=1, value=640, step=1, key=f'detect_width_{i}')
            with col_cam2:
                detect_height = st.number_input(f'Altura de Detecção', min_value=1, value=480, step=1, key=f'detect_height_{i}')
            with col_cam3:
                detect_fps = st.number_input(f'FPS de Detecção', min_value=1, value=10, step=1, key=f'detect_fps_{i}')

            st.markdown(f"**Objetos para rastrear na Câmera {i+1}**")
            objects_to_track = st.multiselect(
                f'Selecione os objetos para rastrear na Câmera {i+1}',
                options=available_objects,
                default=['person'],
                key=f'objects_to_track_{i}'
            )

            # Adiciona a configuração da câmera à lista
            camera_config = {
                'name': camera_name,
                'path': camera_path,
                'detect_width': detect_width,
                'detect_height': detect_height,
                'detect_fps': detect_fps,
                'objects_to_track': objects_to_track
            }

            camera_list.append(camera_config)

        submit_frigate = st.form_submit_button('Gerar Configuração')

    if submit_frigate:
        if mqtt_host and mqtt_user and mqtt_password:
            # Monta o dicionário de configuração
            frigate_config = {}

            frigate_config['mqtt'] = {
                'host': mqtt_host,
                'user': mqtt_user,
                'password': mqtt_password
            }

            frigate_config['cameras'] = {}

            for cam in camera_list:
                camera_name = cam['name']
                frigate_config['cameras'][camera_name] = {
                    'ffmpeg': {
                        'inputs': [
                            {
                                'path': cam['path'],
                                'roles': ['detect']
                            }
                        ]
                    },
                    'detect': {
                        'width': cam['detect_width'],
                        'height': cam['detect_height'],
                        'fps': cam['detect_fps']
                    },
                    'objects': {
                        'track': cam['objects_to_track']
                    },
                    'snapshots': {
                        'enabled': True,
                        'timestamp': False,
                        'bounding_box': True,
                        'retain': {
                            'default': 2
                        }
                    }
                }

            # Adiciona configurações padrão (ajuste conforme necessário)
            frigate_config['detectors'] = {
                'cpu': {
                    'type': 'cpu'
                }
            }

            frigate_config['version'] = '0.14.0'  # Atualize para a versão que estiver usando

            # Gera o YAML sem anotações específicas do Python
            frigate_yaml = yaml.safe_dump(frigate_config, sort_keys=False, default_flow_style=False)

            st.markdown("### Configuração Gerada (`frigate.yml`):")
            st.code(frigate_yaml, language='yaml')

            st.markdown("#### Instruções para Uso:")
            st.markdown("""
            - Copie o conteúdo acima e cole em um arquivo chamado `frigate.yml` na pasta de configuração do seu Home Assistant.
            - Certifique-se de que as URLs das câmeras estão corretas e acessíveis pelo Frigate.
            - Reinicie o Frigate para aplicar as novas configurações.
            """)
        else:
            st.warning('Por favor, preencha as informações do MQTT (host, usuário e senha).')


elif navPage == 'Floorplan Helper':


    def render_js():
        # JavaScript para capturar coordenadas
        js_code = """
        <script>
        document.addEventListener("DOMContentLoaded", function () {
            const imgElement = document.getElementById("image-to-map");
            const coordsDisplay = document.getElementById("coords-display");

            if (imgElement && coordsDisplay) {
                imgElement.addEventListener("click", function (event) {
                    const rect = imgElement.getBoundingClientRect();
                    const left = ((event.clientX - rect.left) / rect.width) * 100;
                    const top = ((event.clientY - rect.top) / rect.height) * 100;

                    coordsDisplay.textContent = `left: ${left.toFixed(2)}%; top: ${top.toFixed(2)}%;`;
                    coordsDisplay.style.visibility = "visible";
                });
            }
        });
        </script>
        """
        return js_code

    # Inicializa o estado da sessão para left e top
    if "left" not in st.session_state:
        st.session_state["left"] = "50.00"
    if "top" not in st.session_state:
        st.session_state["top"] = "50.00"

    # Página principal
    st.title("Mapa de Coordenadas para Imagem")

    st.markdown("""
    ### Instruções:
    1. Insira as dimensões exatas da imagem (Largura x Altura) em pixels.
    2. Faça upload da imagem.
    3. Clique na imagem para capturar as coordenadas (left/top) relativas.
    4. Use essas coordenadas no cartão Picture-Elements do Home Assistant.
    """)

    # Input para dimensões da imagem
    dimensions = st.text_input("Dimensões da Imagem (Largura x Altura)", value="1920 x 1080", help="Ex.: 1920 x 1080")

    # Processa largura e altura
    try:
        width, height = map(int, dimensions.lower().replace(" ", "").split("x"))
    except ValueError:
        st.error("Por favor, insira as dimensões no formato correto: Largura x Altura (ex.: 1920 x 1080).")
        width, height = 1920, 1080  # Valores padrão

    # Upload da imagem
    uploaded_file = st.file_uploader("Escolha uma imagem para mapear coordenadas", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        # Renderizar imagem carregada
        img_data = uploaded_file.read()
        encoded_img = base64.b64encode(img_data).decode('utf-8')
        img_src = f"data:image/jpeg;base64,{encoded_img}"

        # Renderizar HTML com JavaScript
        st.components.v1.html(f"""
        <div id="image-container" style="position: relative; text-align: center;">
            <img id="image-to-map" src="{img_src}" style="max-width: 100%; height: auto; cursor: crosshair;" />
            <div id="coords-display" style="
                margin-top: 10px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                color: black;
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #ccc;
                border-radius: 8px;
                display: inline-block;
                visibility: hidden;">
                Clique na imagem para ver as coordenadas.
            </div>
            {render_js()}
        """, height=height, scrolling=False)

    # Inputs organizados em colunas
    st.markdown("### Configurações do YAML")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        entity_id = st.text_input("ID da Entidade", value="input_boolean.ss_fp_area_servico", help="Ex.: input_boolean.nome_da_entidade")
    with col2:
        top = st.text_input("Top (%)", value=st.session_state["top"], help="Ex.: 50%")
    with col3:
        left = st.text_input("Left (%)", value=st.session_state["left"], help="Ex.: 50%")
    with col4:
        width = st.text_input("Largura (%)", value="100%", help="Ex.: 100%")

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        image_on = st.text_input("Imagem ON", value="local/floorplan/SS_AREASERVICO_ON_RENDER.png", help="Caminho da imagem para estado ON")
    with col6:
        image_off = st.text_input("Imagem OFF", value="local/floorplan/transparent.png", help="Caminho da imagem para estado OFF")
    with col7:
        icon = st.text_input("Ícone", value="mdi:ceiling-light", help="Ex.: mdi:ceiling-light")
    with col8:
        opacity = st.text_input("Opacidade", value="5", help="Ex.: 5")

    # Gera o YAML com base nos inputs
    yaml_output = f"""
    - type: conditional
      conditions:
       - entity: {entity_id}
         state: "on"
      elements:
       - type: image
       entity: {entity_id}
       style:
        top: 50%
        left: 50%
        width: {width}
        pointer-events: none
    state_image:
    "on": {image_on}
    "off": {image_off}
    - type: state-icon
    entity: {entity_id}
    icon: {icon}
    tap_action:
    action: toggle
    style:
    top: {st.session_state['top']}%
    left: {st.session_state['left']}%
    opacity: {opacity}
    "--mdc-icon-size": 25px
    "--paper-item-icon-color": white
    """

    # Exibe o YAML gerado
    st.markdown("### YAML Gerado:")
    st.code(yaml_output.strip(), language="yaml")

    st.markdown("""
    ### Instruções para Uso:
    1. Copie o YAML gerado acima.
    2. Cole no cartão Picture Elements do seu Home Assistant.
    3. Certifique-se de que os caminhos das imagens estão corretos e que os arquivos existem no local indicado.
    """)
