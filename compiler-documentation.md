# Documentação do Compilador Charcot

## Visão Geral

O compilador Charcot é uma implementação para a linguagem de programação Charcot, uma linguagem específica para aplicações médicas com foco em segurança, desempenho e facilidade de uso. Este documento descreve a arquitetura, funcionalidades e uso do compilador.

## Estrutura do Compilador

O compilador Charcot segue uma arquitetura tradicional de compiladores de várias passagens e é implementado em Python. Ele é composto por sete componentes principais:

1. **Analisador Léxico (Lexer)**
2. **Analisador Sintático (Parser)**
3. **Analisador Semântico**
4. **Gerador de Código LLVM IR**
5. **Otimizador**
6. **Gerador de Código Nativo**
7. **Frontend de Linha de Comando**

### 1. Analisador Léxico (Lexer)

O analisador léxico é responsável por transformar o código-fonte em uma sequência de tokens. Ele reconhece:

- Palavras-chave da linguagem: `patient`, `procedure`, `treatment`, etc.
- Tipos médicos: `Patient`, `BloodTest`, `Prescription`, etc.
- Unidades médicas: `mg`, `kg`, `mmHg`, `bpm`, etc.
- Operadores, delimitadores e literais
- Comentários (de linha e de bloco)
- Datas no formato YYYY-MM-DD

### 2. Analisador Sintático (Parser)

O parser constrói uma Árvore Sintática Abstrata (AST) a partir dos tokens gerados pelo lexer. Ele implementa uma gramática específica para Charcot, incluindo:

- Declarações de pacientes
- Procedimentos médicos
- Protocolos de tratamento
- Caminhos clínicos (similar a switch/case)
- Prescrições médicas
- Expressões com unidades médicas

### 3. Analisador Semântico

O analisador semântico verifica a consistência semântica do programa, incluindo:

- Verificação de escopo e tipos
- Verificação de referências a variáveis e funções
- Verificação de funções incorporadas médicas
- Tabelas de símbolos para rastreamento de variáveis e funções

### 4. Gerador de Código LLVM IR

Transforma a AST validada em código LLVM IR (Intermediate Representation), que é uma representação de baixo nível, mas independente de arquitetura. Implementa:

- Tipos específicos para dados médicos (Patient, Medication, Prescription)
- Chamadas para funções de verificação médica
- Geração de código para construções específicas de Charcot

### 5. Otimizador

Aplica otimizações no código LLVM IR para melhorar o desempenho, incluindo:

- Dobramento de constantes
- Eliminação de código morto
- Eliminação de subexpressões comuns
- Otimizações específicas para aplicações médicas

### 6. Gerador de Código Nativo

Utiliza o backend LLVM para transformar o código IR em código nativo otimizado para a arquitetura alvo, que pode ser:

- x86-64
- ARM
- Outras arquiteturas suportadas pelo LLVM

### 7. Frontend de Linha de Comando

Uma interface de linha de comando para interação com o compilador, oferecendo diversas opções como:

- Compilação para código nativo ou apenas LLVM IR
- Exibição de tokens e AST para depuração
- Controle de otimizações
- Seleção de arquitetura alvo

## Uso do Compilador

### Instalação

O compilador Charcot requer Python 3.6+ e, para a compilação completa até código nativo, requer a instalação do LLVM.

```bash
# Clone o repositório
git clone https://github.com/your-username/charcot-compiler.git
cd charcot-compiler

# Instale as dependências
pip install -r requirements.txt
```

### Compilação Básica

Para compilar um programa Charcot:

```bash
python charcot_compiler.py arquivo.charcot
```

Isso gera um arquivo objeto `arquivo.o` que pode ser linkado com outras bibliotecas.

### Opções de Compilação

```
Uso: charcot_compiler.py [opções] input

Argumentos posicionais:
  input                 Arquivo de entrada (.charcot)

Opções:
  -h, --help            Mostra esta mensagem de ajuda e sai
  -o OUTPUT, --output OUTPUT
                        Arquivo de saída (.o)
  -S, --assembly        Gerar apenas código LLVM IR
  -v, --verbose         Modo verboso
  --dump-ast            Mostrar AST
  --dump-tokens         Mostrar tokens
  --no-optimize         Desabilitar otimizações
  -t TARGET, --target TARGET
                        Arquitetura alvo (default: x86_64)
```

### Exemplos

```bash
# Compilar com saída verbosa
python charcot_compiler.py -v exemplo.charcot

# Gerar apenas código LLVM IR
python charcot_compiler.py -S exemplo.charcot

# Compilar para ARM
python charcot_compiler.py -t arm exemplo.charcot

# Mostrar tokens e AST
python charcot_compiler.py --dump-tokens --dump-ast exemplo.charcot
```

## Resolução de Problemas Comuns

### 1. Erro: "Esperado identificador após '.'"

Este erro ocorre quando uma palavra-chave é usada após um ponto em um caminho de importação. Por exemplo:

```
import medical.patient;
```

Solução: Renomeie o módulo para não usar palavras-chave reservadas:

```
import medical.patient_module;
```

### 2. Erro: "Variável 'X' não definida"

Este erro ocorre quando você tenta usar uma variável que não foi declarada no escopo atual.

Solução: Certifique-se de declarar a variável antes de usá-la:

```
variable_name : tipo = valor;
```

### 3. Erro: "Tipo 'X' desconhecido"

Este erro ocorre quando você usa um tipo que não está definido na linguagem.

Solução: Use um dos tipos internos Charcot ou importe o módulo que define o tipo.

## Limitações Atuais

1. O compilador não suporta completamente todas as otimizações LLVM
2. A biblioteca padrão médica ainda está em desenvolvimento
3. Não há suporte para debugging integrado
4. O sistema de tipos não verifica completamente todas as interações de medicamentos

## Próximos Passos

1. Implementação completa da biblioteca médica padrão
2. Suporte a módulos de terceiros
3. Melhor integração com sistemas hospitalares
4. Interface gráfica para desenvolvimento
5. Validação clínica e certificação

## Contribuindo

Contribuições para o compilador Charcot são bem-vindas. Por favor, siga as diretrizes:

1. Fork o repositório
2. Crie um branch para sua feature (`git checkout -b feature/nome-da-feature`)
3. Faça suas alterações
4. Execute os testes
5. Commit suas alterações (`git commit -m 'Adiciona nova feature'`)
6. Push para o branch (`git push origin feature/nome-da-feature`)
7. Abra um Pull Request

## Licença

O compilador Charcot é licenciado sob a licença MIT.
