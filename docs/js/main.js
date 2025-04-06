/**
 * Charcot Website JavaScript
 * Main functionality for all pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // Setup code tabs on homepage and examples
    setupCodeTabs();
    
    // Setup FAQ accordions
    setupFaqAccordions();
    
    // Setup installation tabs
    setupInstallationTabs();
    
    // Setup playground if present
    if (document.getElementById('editor')) {
        setupPlayground();
    }
});

/**
 * Setup code example tabs
 */
function setupCodeTabs() {
    const tabContainers = document.querySelectorAll('.code-tabs');
    
    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('.code-tab');
        const codeContent = container.nextElementSibling;
        
        if (!codeContent || !codeContent.classList.contains('code-content')) {
            return;
        }
        
        // Get code examples if they exist in data attribute
        let codeExamples = [];
        
        // Check if we have predefined examples in the HTML
        if (codeContent.dataset.examples) {
            try {
                codeExamples = JSON.parse(codeContent.dataset.examples);
            } catch (e) {
                console.error('Error parsing code examples:', e);
            }
        } else {
            // Otherwise, store the initial content as the first example
            codeExamples.push(codeContent.innerHTML);
        }
        
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to the clicked tab
                this.classList.add('active');
                
                // Update code content if we have examples for this tab
                if (codeExamples[index]) {
                    codeContent.innerHTML = codeExamples[index];
                }
            });
        });
    });
}

/**
 * Setup FAQ accordions
 */
function setupFaqAccordions() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        if (question) {
            question.addEventListener('click', () => {
                // Toggle for current item
                item.classList.toggle('active');
            });
        }
    });
}

/**
 * Setup installation tabs
 */
function setupInstallationTabs() {
    // Function to setup tab switching
    function setupTabs(tabsContainer) {
        if (!tabsContainer) return;
        
        const tabs = tabsContainer.querySelectorAll('.tab');
        const tabContents = [];
        
        // Find related content blocks
        let nextElement = tabsContainer.nextElementSibling;
        while (nextElement && nextElement.classList.contains('tab-content')) {
            tabContents.push(nextElement);
            nextElement = nextElement.nextElementSibling;
        }
        
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to clicked tab
                this.classList.add('active');
                
                // Hide all tab contents
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Show corresponding content
                if (tabContents[index]) {
                    tabContents[index].classList.add('active');
                }
            });
        });
    }
    
    // Setup all tab containers on the page
    const tabContainers = document.querySelectorAll('.tabs');
    tabContainers.forEach(setupTabs);
}

/**
 * Setup playground functionality
 */
function setupPlayground() {
    // Get elements
    const editor = document.getElementById('editor');
    const output = document.getElementById('output');
    const lineNumbers = document.querySelector('.editor-line-numbers');
    
    // Generate line numbers
    function updateLineNumbers() {
        if (!lineNumbers) return;
        
        const lineCount = editor.value.split('\n').length;
        let content = '';
        
        for (let i = 1; i <= lineCount; i++) {
            content += i + '<br>';
        }
        
        lineNumbers.innerHTML = content;
    }
    
    // Sync scroll between editor and line numbers
    function syncScroll() {
        if (!lineNumbers) return;
        lineNumbers.scrollTop = editor.scrollTop;
    }
    
    // Run code function
    window.runCode = function() {
        const code = editor.value;
        
        // Clear previous output
        output.innerHTML = '<span class="output-info">// Compilando código Charcot...</span>\n\n';
        
        // Simulate compilation and execution
        setTimeout(() => {
            output.innerHTML += '<span class="output-success">// Compilação concluída com sucesso!</span>\n';
            output.innerHTML += '<span class="output-info">// Executando programa...</span>\n\n';
            
            // Simulate response based on code content
            setTimeout(() => {
                if (code.includes('imprimir("Olá, mundo médico!")')) {
                    output.innerHTML += 'Olá, mundo médico!\n';
                }
                
                if (code.includes('paciente.nome_completo()')) {
                    output.innerHTML += 'Paciente: João Silva\n';
                }
                
                if (code.includes('paciente.idade()')) {
                    output.innerHTML += 'Idade: 45 anos\n';
                }
                
                if (code.includes('calcular_imc')) {
                    output.innerHTML += '\nIMC: 24.5\n';
                    output.innerHTML += 'Classificação: Peso normal\n';
                }
                
                if (code.includes('verificar_interacao')) {
                    output.innerHTML += '\nINTERAÇÃO ENCONTRADA:\n';
                    output.innerHTML += 'ATENÇÃO: Interação entre Warfarina e Paracetamol\n';
                    output.innerHTML += 'Tipo: Farmacodinâmica\n';
                    output.innerHTML += 'Gravidade: Moderada\n';
                    output.innerHTML += 'Efeito: Aumento do risco de sangramento\n';
                    output.innerHTML += 'Recomendação: Monitorar INR e ajustar dose conforme necessário\n';
                }
                
                if (code.includes('erro') || code.includes('ERRO')) {
                    output.innerHTML += '<span class="output-error">\nErro: Operação não permitida\nEm: linha 12, coluna 5\nDetalhes: Verificação de segurança falhou</span>\n';
                }
                
                // Scroll to the end of output
                output.scrollTop = output.scrollHeight;
            }, 500);
        }, 700);
    };
    
    // Load example code
    window.loadExample = function(exampleId) {
        // Fetch example code from server
        // For demonstration, examples are defined below
        let code = exampleLibrary[exampleId] || '';
        
        // Set code in editor
        editor.value = code;
        
        // Update line numbers
        updateLineNumbers();
        
        // Clear output
        output.innerHTML = '<span class="output-info">// Código carregado com sucesso.\n// Clique em "Executar" para ver o resultado.</span>';
    };
    
    // Share code
    window.shareCode = function() {
        const code = editor.value;
        // Encode code in base64
        const encodedCode = btoa(encodeURIComponent(code));
        // Create URL to share
        const shareUrl = `${window.location.origin}${window.location.pathname}?code=${encodedCode}`;
        
        // Show in output
        output.innerHTML = '<span class="output-info">// Link para compartilhar este código:</span>\n\n';
        output.innerHTML += shareUrl + '\n\n';
        output.innerHTML += '<span class="output-info">// O link foi copiado para a área de transferência.</span>';
        
        // Copy to clipboard
        navigator.clipboard.writeText(shareUrl).catch(err => {
            console.error('Error copying to clipboard', err);
        });
    };
    
    // Download code
    window.downloadCode = function() {
        const code = editor.value;
        const blob = new Blob([code], {type: 'text/plain'});
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'codigo_charcot.chc';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Show confirmation
        output.innerHTML = '<span class="output-info">// Código baixado como "codigo_charcot.chc"</span>';
    };
    
    // Clear code
    window.clearCode = function() {
        if (confirm('Tem certeza que deseja limpar o código?')) {
            editor.value = '';
            output.innerHTML = '<span class="output-info">// Área de código limpa.</span>';
            updateLineNumbers();
        }
    };
    
    // Check for code in URL
    const urlParams = new URLSearchParams(window.location.search);
    const codeParam = urlParams.get('code');
    
    if (codeParam) {
        try {
            const decodedCode = decodeURIComponent(atob(codeParam));
            editor.value = decodedCode;
            output.innerHTML = '<span class="output-info">// Código carregado da URL compartilhada.\n// Clique em "Executar" para ver o resultado.</span>';
        } catch (e) {
            console.error('Error decoding code from URL', e);
        }
    }
    
    // Add event listeners
    if (editor) {
        editor.addEventListener('input', updateLineNumbers);
        editor.addEventListener('scroll', syncScroll);
    }
    
    // Initialize line numbers
    updateLineNumbers();
}

/**
 * Example code library for playground
 */
const exampleLibrary = {
    'hello-world': `// Exemplo simples em Charcot
usar padrao::io;

func principal() {
    imprimir("Olá, mundo médico!");
    
    let nome = "Charcot";
    let versao = 0.1;
    
    imprimir(f"Linguagem {nome} versão {versao}");
    imprimir("Projetada para aplicações médicas seguras");
}`,
    
    'imc-calculator': `// Calculadora de IMC em Charcot
usar paciente::dados_antropometricos;

// Tipos com verificação integrada
tipo Peso = Decimal<0.1..635.0, "kg">; // Intervalo válido com unidade
tipo Altura = Decimal<0.3..2.5, "m">;
tipo IMC = Decimal<10.0..70.0, "kg/m²">;

// Enumeração para classificação
enum ClassificacaoIMC {
    BaixoPeso,
    PesoNormal,
    Sobrepeso,
    Obesidade1,
    Obesidade2,
    Obesidade3,
}

// Função com tipos validados
func calcular_imc(peso: Peso, altura: Altura) -> IMC {
    // Não é necessário validar entradas - o sistema de tipos garante valores válidos
    let imc_valor = peso.valor() / (altura.valor() * altura.valor());
    IMC::novo(arredondar(imc_valor, 1))
}

// Classificação com segurança de tipos
func classificar_imc(imc: IMC) -> ClassificacaoIMC {
    match imc.valor() {
        < 18.5 => ClassificacaoIMC::BaixoPeso,
        < 25.0 => ClassificacaoIMC::PesoNormal,
        < 30.0 => ClassificacaoIMC::Sobrepeso,
        < 35.0 => ClassificacaoIMC::Obesidade1,
        < 40.0 => ClassificacaoIMC::Obesidade2,
        _ => ClassificacaoIMC::Obesidade3,
    }
}

func principal() {
    // Criar valores seguros com unidades
    let peso = Peso::novo(70.5); // 70.5 kg
    let altura = Altura::novo(1.75); // 1.75 m
    
    // Calcular IMC
    let imc = calcular_imc(peso, altura);
    let classificacao = classificar_imc(imc);
    
    // Exibir resultados
    imprimir(f"IMC: {imc}");
    
    // Imprimir classificação
    match classificacao {
        ClassificacaoIMC::BaixoPeso => imprimir("Classificação: Baixo peso"),
        ClassificacaoIMC::PesoNormal => imprimir("Classificação: Peso normal"),
        ClassificacaoIMC::Sobrepeso => imprimir("Classificação: Sobrepeso"),
        ClassificacaoIMC::Obesidade1 => imprimir("Classificação: Obesidade grau I"),
        ClassificacaoIMC::Obesidade2 => imprimir("Classificação: Obesidade grau II"),
        ClassificacaoIMC::Obesidade3 => imprimir("Classificação: Obesidade grau III"),
    }
}`,

    'medical-types': `// Demonstração de tipos médicos em Charcot
usar paciente::sinais_vitais;

// Definição de tipos com validação integrada
tipo TemperaturaCorporal = Decimal<35.0..42.0, "°C">;
tipo FrequenciaCardiaca = Int<30..220, "bpm">;
tipo PressaoSistolica = Int<70..250, "mmHg">;
tipo PressaoDiastolica = Int<40..150, "mmHg">;
tipo SaturacaoO2 = Decimal<70.0..100.0, "%">;

// Estrutura para registro de sinais vitais
struct RegistroVitais {
    temperatura: TemperaturaCorporal,
    freq_cardiaca: FrequenciaCardiaca,
    pressao_sistolica: PressaoSistolica,
    pressao_diastolica: PressaoDiastolica,
    saturacao: SaturacaoO2,
    
    // Verificação de relação entre valores
    verify {
        self.pressao_sistolica > self.pressao_diastolica
    }
}

// Enum para gravidade de alertas
enum Gravidade {
    Normal,
    Atencao,
    Urgente,
    Emergencia,
}

// Função para classificar temperatura
func classificar_temperatura(temp: TemperaturaCorporal) -> Gravidade {
    match temp.valor() {
        < 36.0 => Gravidade::Atencao,
        36.0..37.5 => Gravidade::Normal,
        37.6..38.5 => Gravidade::Atencao,
        38.6..39.5 => Gravidade::Urgente,
        _ => Gravidade::Emergencia
    }
}

func principal() {
    // Criação de valores seguros
    let temp = TemperaturaCorporal::novo(37.8);
    let fc = FrequenciaCardiaca::novo(85);
    let ps = PressaoSistolica::novo(120);
    let pd = PressaoDiastolica::novo(80);
    let sat = SaturacaoO2::novo(98.5);
    
    // Criação de registro com verificação automática
    let vitais = RegistroVitais {
        temperatura: temp,
        freq_cardiaca: fc,
        pressao_sistolica: ps,
        pressao_diastolica: pd,
        saturacao: sat,
    };
    
    // Análise de valores
    let status_temp = classificar_temperatura(vitais.temperatura);
    
    // Exibir informações
    imprimir("=== Sinais Vitais ===");
    imprimir(f"Temperatura: {vitais.temperatura}");
    imprimir(f"Freq. Cardíaca: {vitais.freq_cardiaca}");
    imprimir(f"Pressão Arterial: {vitais.pressao_sistolica}/{vitais.pressao_diastolica}");
    imprimir(f"Saturação O2: {vitais.saturacao}");
    
    match status_temp {
        Gravidade::Normal => imprimir("\\nStatus: NORMAL"),
        Gravidade::Atencao => imprimir("\\nStatus: ATENÇÃO - Febre baixa"),
        Gravidade::Urgente => imprimir("\\nStatus: URGENTE - Febre alta"),
        Gravidade::Emergencia => imprimir("\\nStatus: EMERGÊNCIA - Hipertermia crítica"),
    }
}`
    // Additional examples could be added here
};
