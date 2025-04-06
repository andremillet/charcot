#!/usr/bin/env python3
"""
Compilador para a Linguagem de Programação Charcot

Este compilador transforma código fonte Charcot em código LLVM IR,
que pode então ser compilado para código nativo de alta performance.
"""

import os
import sys
import re
import json
import argparse
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple, Any

#################################################
# PARTE 1: TOKENIZAÇÃO (ANÁLISE LÉXICA)
#################################################

class TokenType(Enum):
    # Palavras-chave
    PATIENT = auto()
    PROCEDURE = auto()
    TREATMENT = auto()
    PRESCRIPTION = auto()
    VERIFY = auto()
    IMPORT = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    FOREACH = auto()
    IN = auto()
    RETURN = auto()
    CASE = auto()
    CLINICAL_PATH = auto()
    DIAGNOSE = auto()
    MONITOR = auto()
    PRESCRIBE = auto()
    NEW = auto()
    
    # Tipos
    TYPE = auto()  # Para Patient, BloodTest, etc
    
    # Literais
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    DATE = auto()
    MEASUREMENT = auto()  # 120/80mmHg, 5mg, etc.
    
    # Operadores
    ASSIGN = auto()  # :=, =
    COLON = auto()  # :
    DOT = auto()  # .
    COMMA = auto()  # ,
    PLUS = auto()  # +
    MINUS = auto()  # -
    TIMES = auto()  # *
    DIVIDE = auto()  # /
    GT = auto()  # >
    LT = auto()  # <
    GTE = auto()  # >=
    LTE = auto()  # <=
    EQ = auto()  # ==
    NEQ = auto()  # !=
    AND = auto()  # &&
    OR = auto()  # ||
    NOT = auto()  # !
    
    # Delimitadores
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    SEMICOLON = auto()  # ;
    
    # Especial
    EOF = auto()
    COMMENT = auto()

class Token:
    def __init__(self, token_type: TokenType, value: str, line: int, column: int):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Token({self.type}, '{self.value}', line={self.line}, col={self.column})"
    
    def __repr__(self):
        return self.__str__()

class Lexer:
    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.current_char = self.source[0] if self.source else None
        
        # Mapeia palavras-chave para tipos de token
        self.keywords = {
            'patient': TokenType.PATIENT,
            'procedure': TokenType.PROCEDURE,
            'treatment': TokenType.TREATMENT,
            'prescription': TokenType.PRESCRIPTION,
            'verify': TokenType.VERIFY,
            'import': TokenType.IMPORT,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'while': TokenType.WHILE,
            'for': TokenType.FOR,
            'foreach': TokenType.FOREACH,
            'in': TokenType.IN,
            'return': TokenType.RETURN,
            'case': TokenType.CASE,
            'clinical_path': TokenType.CLINICAL_PATH,
            'diagnose': TokenType.DIAGNOSE,
            'monitor': TokenType.MONITOR,
            'prescribe': TokenType.PRESCRIBE,
            'new': TokenType.NEW
        }
        
        # Tipos médicos comuns
        self.medical_types = {
            'Patient', 'BloodTest', 'VitalSigns', 'Prescription',
            'Medication', 'LabResult', 'Diagnosis', 'Treatment'
        }
        
        # Unidades médicas para medições
        self.medical_units = {
            'mg', 'g', 'kg', 'mmHg', 'bpm', 'mmol', 'μmol', 'mL', 'L',
            'mg/dL', 'mEq/L', 'ng/mL', 'U/L', 'mmol/L', 'cm', 'm',
            'years', 'days', 'hours', 'h', 'min', 'C', 'F'
        }
    
    def advance(self):
        """Avança para o próximo caractere."""
        self.position += 1
        
        if self.position >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.position]
            
            if self.current_char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
    
    def peek(self, n=1) -> Optional[str]:
        """Verifica o caractere n posições à frente sem avançar."""
        peek_pos = self.position + n
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]
    
    def skip_whitespace(self):
        """Pula espaços em branco."""
        while self.current_char is not None and self.current_char.isspace():
            self.advance()
    
    def skip_comment(self):
        """Pula comentários de linha (// ...) e blocos (/* ... */)."""
        if self.current_char == '/' and self.peek() == '/':
            # Comentário de linha
            while self.current_char is not None and self.current_char != '\n':
                self.advance()
        elif self.current_char == '/' and self.peek() == '*':
            # Comentário de bloco
            self.advance()  # Pula '/'
            self.advance()  # Pula '*'
            
            while True:
                if self.current_char is None:
                    break
                if self.current_char == '*' and self.peek() == '/':
                    self.advance()  # Pula '*'
                    self.advance()  # Pula '/'
                    break
                self.advance()
    
    def identifier(self) -> Token:
        """Processa identificadores e palavras-chave."""
        start_col = self.column
        result = ''
        
        while (self.current_char is not None and 
               (self.current_char.isalnum() or self.current_char == '_')):
            result += self.current_char
            self.advance()
        
        # Verifica se é uma palavra-chave
        if result in self.keywords:
            return Token(self.keywords[result], result, self.line, start_col)
        # Verifica se é um tipo médico
        elif result in self.medical_types:
            return Token(TokenType.TYPE, result, self.line, start_col)
        # Senão, é um identificador genérico
        else:
            return Token(TokenType.IDENTIFIER, result, self.line, start_col)
    
    def number(self) -> Token:
        """Processa números (inteiros e decimais)."""
        start_col = self.column
        result = ''
        
        # Processa parte inteira
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        
        # Processa parte decimal se houver
        if self.current_char == '.':
            result += self.current_char
            self.advance()
            
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()
        
        # Verifica se o número é seguido por uma unidade médica
        unit = ''
        peek_pos = 0
        
        # Para lidar com notações como "120/80mmHg"
        if self.current_char == '/':
            unit += self.current_char
            self.advance()
            
            while self.current_char is not None and self.current_char.isdigit():
                unit += self.current_char
                self.advance()
        
        # Captura a unidade
        start_unit_pos = self.position
        while (self.current_char is not None and 
              (self.current_char.isalpha() or self.current_char == '/')):
            unit += self.current_char
            self.advance()
        
        # Verifica se a unidade é uma unidade médica conhecida
        if unit in self.medical_units:
            return Token(TokenType.MEASUREMENT, f"{result}{unit}", self.line, start_col)
        elif unit:  # Tem unidade, mas não é reconhecida
            # Restauramos a posição para o início da unidade para reprocessá-la
            self.position = start_unit_pos
            self.current_char = self.source[self.position] if self.position < len(self.source) else None
        
        return Token(TokenType.NUMBER, result, self.line, start_col)
    
    def string(self) -> Token:
        """Processa strings (entre aspas)."""
        start_col = self.column
        self.advance()  # Pula a aspa inicial
        result = ''
        
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()  # Pula o escape
                if self.current_char == 'n':
                    result += '\n'
                elif self.current_char == 't':
                    result += '\t'
                elif self.current_char == 'r':
                    result += '\r'
                else:
                    result += self.current_char
            else:
                result += self.current_char
            self.advance()
        
        if self.current_char == '"':
            self.advance()  # Pula a aspa final
        else:
            raise SyntaxError(f"String não terminada na linha {self.line}, coluna {start_col}")
        
        return Token(TokenType.STRING, result, self.line, start_col)
    
    def date(self) -> Optional[Token]:
        """Tenta processar uma data no formato YYYY-MM-DD."""
        start_col = self.column
        start_pos = self.position
        
        # Padrão de data simples: YYYY-MM-DD
        date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
        
        # Verifica se temos um padrão de data a partir da posição atual
        match = date_pattern.match(self.source[start_pos:])
        
        if match:
            date_str = match.group(0)
            
            # Avança o lexer após a data
            for _ in range(len(date_str)):
                self.advance()
            
            return Token(TokenType.DATE, date_str, self.line, start_col)
        
        return None
    
    def get_next_token(self) -> Token:
        """Obtém o próximo token do código-fonte."""
        while self.current_char is not None:
            
            # Ignora espaços em branco
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            # Ignora comentários
            if self.current_char == '/' and (self.peek() == '/' or self.peek() == '*'):
                self.skip_comment()
                continue
            
            # Identificadores e palavras-chave
            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()
            
            # Datas (YYYY-MM-DD)
            if self.current_char.isdigit() and self.peek() and self.peek(2) and self.peek(3):
                peek_str = self.current_char + self.peek() + self.peek(2) + self.peek(3)
                if re.match(r'\d{4}-', peek_str):
                    date_token = self.date()
                    if date_token:
                        return date_token
            
            # Números
            if self.current_char.isdigit():
                return self.number()
            
            # Strings
            if self.current_char == '"':
                return self.string()
            
            # Operadores e delimitadores
            if self.current_char == ':':
                col = self.column
                self.advance()
                
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.ASSIGN, ':=', self.line, col)
                else:
                    return Token(TokenType.COLON, ':', self.line, col)
            
            if self.current_char == '=':
                col = self.column
                self.advance()
                
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.EQ, '==', self.line, col)
                else:
                    return Token(TokenType.ASSIGN, '=', self.line, col)
            
            if self.current_char == '!':
                col = self.column
                self.advance()
                
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.NEQ, '!=', self.line, col)
                else:
                    return Token(TokenType.NOT, '!', self.line, col)
            
            if self.current_char == '>':
                col = self.column
                self.advance()
                
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.GTE, '>=', self.line, col)
                else:
                    return Token(TokenType.GT, '>', self.line, col)
            
            if self.current_char == '<':
                col = self.column
                self.advance()
                
                if self.current_char == '=':
                    self.advance()
                    return Token(TokenType.LTE, '<=', self.line, col)
                else:
                    return Token(TokenType.LT, '<', self.line, col)
            
            if self.current_char == '&' and self.peek() == '&':
                col = self.column
                self.advance()
                self.advance()
                return Token(TokenType.AND, '&&', self.line, col)
            
            if self.current_char == '|' and self.peek() == '|':
                col = self.column
                self.advance()
                self.advance()
                return Token(TokenType.OR, '||', self.line, col)
            
            # Caracteres simples
            char_tokens = {
                '.': TokenType.DOT,
                ',': TokenType.COMMA,
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.TIMES,
                '/': TokenType.DIVIDE,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ';': TokenType.SEMICOLON
            }
            
            if self.current_char in char_tokens:
                col = self.column
                char = self.current_char
                self.advance()
                return Token(char_tokens[char], char, self.line, col)
            
            # Se chegou aqui, encontrou um caractere desconhecido
            raise SyntaxError(
                f"Caractere inesperado '{self.current_char}' na linha {self.line}, coluna {self.column}"
            )
        
        # Fim do arquivo
        return Token(TokenType.EOF, '', self.line, self.column)

    def tokenize(self) -> List[Token]:
        """Tokeniza todo o código-fonte."""
        tokens = []
        token = self.get_next_token()
        
        while token.type != TokenType.EOF:
            tokens.append(token)
            token = self.get_next_token()
        
        tokens.append(token)  # Adiciona o token EOF
        return tokens


#################################################
# PARTE 2: ANÁLISE SINTÁTICA (PARSER)
#################################################

class ASTNode:
    """Classe base para todos os nós da AST (Árvore Sintática Abstrata)."""
    pass

class Program(ASTNode):
    """Nó raiz da AST, representando um programa completo."""
    def __init__(self, declarations):
        self.declarations = declarations

class ImportDeclaration(ASTNode):
    """Declaração de importação de módulo."""
    def __init__(self, module_name):
        self.module_name = module_name

class VariableDeclaration(ASTNode):
    """Declaração de variável com tipo opcional."""
    def __init__(self, name, type_name=None, value=None):
        self.name = name
        self.type_name = type_name
        self.value = value

class PatientDeclaration(ASTNode):
    """Declaração de paciente."""
    def __init__(self, name, properties):
        self.name = name
        self.properties = properties

class ProcedureDeclaration(ASTNode):
    """Declaração de procedimento (função)."""
    def __init__(self, name, parameters, body):
        self.name = name
        self.parameters = parameters
        self.body = body

class TreatmentDeclaration(ASTNode):
    """Declaração de protocolo de tratamento."""
    def __init__(self, name, parameters, body):
        self.name = name
        self.parameters = parameters
        self.body = body

class Parameter(ASTNode):
    """Parâmetro de função/procedimento."""
    def __init__(self, name, type_name=None):
        self.name = name
        self.type_name = type_name

class BlockStatement(ASTNode):
    """Bloco de declarações entre chaves {}."""
    def __init__(self, statements):
        self.statements = statements

class IfStatement(ASTNode):
    """Declaração condicional if/else."""
    def __init__(self, condition, if_body, else_body=None):
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body

class WhileStatement(ASTNode):
    """Declaração de loop while."""
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class ForEachStatement(ASTNode):
    """Declaração de loop foreach."""
    def __init__(self, variable, collection, body):
        self.variable = variable
        self.collection = collection
        self.body = body

class ClinicalPathStatement(ASTNode):
    """Declaração de caminho clínico (similar a switch/case)."""
    def __init__(self, expression, cases):
        self.expression = expression
        self.cases = cases

class CaseStatement(ASTNode):
    """Caso em uma declaração de caminho clínico."""
    def __init__(self, value, body):
        self.value = value
        self.body = body

class ReturnStatement(ASTNode):
    """Declaração de retorno."""
    def __init__(self, value=None):
        self.value = value

class ExpressionStatement(ASTNode):
    """Declaração que consiste apenas em uma expressão."""
    def __init__(self, expression):
        self.expression = expression

class PrescribeStatement(ASTNode):
    """Declaração de prescrição de medicamento."""
    def __init__(self, patient, medication, dose, instructions=None, duration=None):
        self.patient = patient
        self.medication = medication
        self.dose = dose
        self.instructions = instructions
        self.duration = duration

class BinaryOperation(ASTNode):
    """Operação binária (a + b, a > b, etc)."""
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class UnaryOperation(ASTNode):
    """Operação unária (!a, -b, etc)."""
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand

class VariableReference(ASTNode):
    """Referência a uma variável."""
    def __init__(self, name):
        self.name = name

class PropertyAccess(ASTNode):
    """Acesso a uma propriedade (obj.prop)."""
    def __init__(self, object_expr, property_name):
        self.object_expr = object_expr
        self.property_name = property_name

class FunctionCall(ASTNode):
    """Chamada de função/procedimento."""
    def __init__(self, name, arguments=None):
        self.name = name
        self.arguments = arguments or []

class MethodCall(ASTNode):
    """Chamada de método (obj.method())."""
    def __init__(self, object_expr, method_name, arguments=None):
        self.object_expr = object_expr
        self.method_name = method_name
        self.arguments = arguments or []

class Literal(ASTNode):
    """Valor literal (número, string, etc)."""
    def __init__(self, value, literal_type):
        self.value = value
        self.literal_type = literal_type

class ArrayLiteral(ASTNode):
    """Lista de valores."""
    def __init__(self, elements):
        self.elements = elements

class ObjectLiteral(ASTNode):
    """Objeto literal com pares chave-valor."""
    def __init__(self, properties):
        self.properties = properties

class PropertyAssignment(ASTNode):
    """Atribuição de propriedade em um objeto literal."""
    def __init__(self, name, value):
        self.name = name
        self.value = value

class Parser:
    """
    Analisador sintático para a linguagem Charcot.
    Constrói uma Árvore Sintática Abstrata (AST) a partir de uma lista de tokens.
    """
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.tokens[0]
    
    def error(self, message):
        """Levanta um erro de sintaxe com uma mensagem específica."""
        token = self.current_token
        raise SyntaxError(
            f"{message} na linha {token.line}, coluna {token.column}, " +
            f"encontrado '{token.value}' ({token.type})"
        )
    
    def eat(self, token_type):
        """
        Consome o token atual se for do tipo esperado,
        avançando para o próximo token.
        """
        if self.current_token.type == token_type:
            self.current_token_index += 1
            if self.current_token_index < len(self.tokens):
                self.current_token = self.tokens[self.current_token_index]
            return
        self.error(f"Esperado {token_type}, mas encontrado {self.current_token.type}")
    
    def peek(self, offset=1):
        """Verifica um token à frente sem consumir o token atual."""
        peek_index = self.current_token_index + offset
        if peek_index < len(self.tokens):
            return self.tokens[peek_index]
        return None
    
    def parse(self):
        """Ponto de entrada principal do parser."""
        return self.program()
    
    def program(self):
        """
        program : declaration* EOF
        """
        declarations = []
        
        while self.current_token.type != TokenType.EOF:
            declarations.append(self.declaration())
        
        return Program(declarations)
    
    def declaration(self):
        """
        declaration : import_declaration
                    | variable_declaration
                    | patient_declaration
                    | procedure_declaration
                    | treatment_declaration
        """
        if self.current_token.type == TokenType.IMPORT:
            return self.import_declaration()
        elif self.current_token.type == TokenType.PATIENT:
            return self.patient_declaration()
        elif self.current_token.type == TokenType.PROCEDURE:
            return self.procedure_declaration()
        elif self.current_token.type == TokenType.TREATMENT:
            return self.treatment_declaration()
        else:
            return self.variable_declaration()
    
    def import_declaration(self):
        """
        import_declaration : 'import' identifier ('.' identifier)* ';'
        """
        self.eat(TokenType.IMPORT)
        
        if self.current_token.type != TokenType.IDENTIFIER:
            self.error("Esperado identificador após 'import'")
        
        module_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        while self.current_token.type == TokenType.DOT:
            self.eat(TokenType.DOT)
            if self.current_token.type != TokenType.IDENTIFIER:
                self.error("Esperado identificador após '.'")
            
            module_name += "." + self.current_token.value
            self.eat(TokenType.IDENTIFIER)
        
        self.eat(TokenType.SEMICOLON)
        
        return ImportDeclaration(module_name)
    
    def variable_declaration(self):
        """
        variable_declaration : identifier (':' type_name)? ('=' expression)? ';'
        """
        variable_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        type_name = None
        if self.current_token.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            
            if self.current_token.type == TokenType.TYPE:
                type_name = self.current_token.value
                self.eat(TokenType.TYPE)
            elif self.current_token.type == TokenType.IDENTIFIER:
                type_name = self.current_token.value
                self.eat(TokenType.IDENTIFIER)
            else:
                self.error("Esperado tipo após ':'")
        
        value = None
        if self.current_token.type == TokenType.ASSIGN:
            self.eat(TokenType.ASSIGN)
            value = self.expression()
        
        self.eat(TokenType.SEMICOLON)
        
        return VariableDeclaration(variable_name, type_name, value)
    
    def patient_declaration(self):
        """
        patient_declaration : 'patient' identifier ':' 'Patient' '{' property_list '}'
        """
        self.eat(TokenType.PATIENT)
        
        if self.current_token.type != TokenType.IDENTIFIER:
            self.error("Esperado identificador após 'patient'")
        
        patient_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        self.eat(TokenType.COLON)
        
        if self.current_token.type != TokenType.TYPE or self.current_token.value != "Patient":
            self.error("Esperado tipo 'Patient' após ':'")
        
        self.eat(TokenType.TYPE)
        
        self.eat(TokenType.LBRACE)
        
        properties = self.property_list()
        
        self.eat(TokenType.RBRACE)
        
        return PatientDeclaration(patient_name, properties)
    
    def property_list(self):
        """
        property_list : (property_assignment (',' property_assignment)*)? ','?
        """
        properties = []
        
        if self.current_token.type != TokenType.RBRACE:
            properties.append(self.property_assignment())
            
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                
                # Permite uma vírgula final (trailing comma)
                if self.current_token.type == TokenType.RBRACE:
                    break
                
                properties.append(self.property_assignment())
        
        return properties
    
    def property_assignment(self):
        """
        property_assignment : identifier ':' expression
        """
        prop_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        self.eat(TokenType.COLON)
        
        prop_value = self.expression()
        
        return PropertyAssignment(prop_name, prop_value)
    
    def procedure_declaration(self):
        """
        procedure_declaration : 'procedure' identifier '(' parameter_list ')' block_statement
        """
        self.eat(TokenType.PROCEDURE)
        
        if self.current_token.type != TokenType.IDENTIFIER:
            self.error("Esperado identificador após 'procedure'")
        
        procedure_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        self.eat(TokenType.LPAREN)
        parameters = self.parameter_list()
        self.eat(TokenType.RPAREN)
        
        body = self.block_statement()
        
        return ProcedureDeclaration(procedure_name, parameters, body)
    
    def treatment_declaration(self):
        """
        treatment_declaration : 'treatment' identifier '(' parameter_list ')' block_statement
        """
        self.eat(TokenType.TREATMENT)
        
        if self.current_token.type != TokenType.IDENTIFIER:
            self.error("Esperado identificador após 'treatment'")
        
        treatment_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        self.eat(TokenType.LPAREN)
        parameters = self.parameter_list()
        self.eat(TokenType.RPAREN)
        
        body = self.block_statement()
        
        return TreatmentDeclaration(treatment_name, parameters, body)
    
    def parameter_list(self):
        """
        parameter_list : (parameter (',' parameter)*)?
        """
        parameters = []
        
        if self.current_token.type != TokenType.RPAREN:
            parameters.append(self.parameter())
            
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                parameters.append(self.parameter())
        
        return parameters
    
    def parameter(self):
        """
        parameter : identifier (':' type_name)?
        """
        if self.current_token.type != TokenType.IDENTIFIER:
            self.error("Esperado identificador no parâmetro")
        
        param_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        type_name = None
        if self.current_token.type == TokenType.COLON:
            self.eat(TokenType.COLON)
            
            if self.current_token.type == TokenType.TYPE:
                type_name = self.current_token.value
                self.eat(TokenType.TYPE)
            elif self.current_token.type == TokenType.IDENTIFIER:
                type_name = self.current_token.value
                self.eat(TokenType.IDENTIFIER)
            else:
                self.error("Esperado tipo após ':'")
        
        return Parameter(param_name, type_name)
    
    def block_statement(self):
        """
        block_statement : '{' statement* '}'
        """
        self.eat(TokenType.LBRACE)
        
        statements = []
        while self.current_token.type != TokenType.RBRACE:
            statements.append(self.statement())
        
        self.eat(TokenType.RBRACE)
        
        return BlockStatement(statements)
    
    def statement(self):
        """
        statement : block_statement
                  | variable_declaration
                  | if_statement
                  | while_statement
                  | foreach_statement
                  | clinical_path_statement
                  | return_statement
                  | expression_statement
                  | prescribe_statement
        """
        if self.current_token.type == TokenType.LBRACE:
            return self.block_statement()
        elif self.current_token.type == TokenType.IF:
            return self.if_statement()
        elif self.current_token.type == TokenType.WHILE:
            return self.while_statement()
        elif self.current_token.type == TokenType.FOREACH:
            return self.foreach_statement()
        elif self.current_token.type == TokenType.CLINICAL_PATH:
            return self.clinical_path_statement()
        elif self.current_token.type == TokenType.RETURN:
            return self.return_statement()
        elif self.current_token.type == TokenType.PRESCRIBE:
            return self.prescribe_statement()
        elif (self.current_token.type == TokenType.IDENTIFIER and
              self.peek().type == TokenType.COLON):
            return self.variable_declaration()
        else:
            return self.expression_statement()
    
    def if_statement(self):
        """
        if_statement : 'if' '(' expression ')' statement ('else' statement)?
        """
        self.eat(TokenType.IF)
        
        self.eat(TokenType.LPAREN)
        condition = self.expression()
        self.eat(TokenType.RPAREN)
        
        if_body = self.statement()
        
        else_body = None
        if self.current_token.type == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            else_body = self.statement()
        
        return IfStatement(condition, if_body, else_body)
    
    def while_statement(self):
        """
        while_statement : 'while' '(' expression ')' statement
        """
        self.eat(TokenType.WHILE)
        
        self.eat(TokenType.LPAREN)
        condition = self.expression()
        self.eat(TokenType.RPAREN)
        
        body = self.statement()
        
        return WhileStatement(condition, body)
    
    def foreach_statement(self):
        """
        foreach_statement : 'foreach' '(' (identifier | variable_declaration) 'in' expression ')' statement
        """
        self.eat(TokenType.FOREACH)
        
        self.eat(TokenType.LPAREN)
        
        # Pode ser uma variável existente ou uma nova declaração
        if (self.current_token.type == TokenType.IDENTIFIER and
            self.peek().type == TokenType.COLON):
            variable = self.variable_declaration()
        else:
            variable_name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)
            variable = VariableReference(variable_name)
        
        self.eat(TokenType.IN)
        
        collection = self.expression()
        
        self.eat(TokenType.RPAREN)
        
        body = self.statement()
        
        return ForEachStatement(variable, collection, body)
    
    def clinical_path_statement(self):
        """
        clinical_path_statement : 'clinical_path' expression '{' case_statement* '}'
        """
        self.eat(TokenType.CLINICAL_PATH)
        
        expression = self.expression()
        
        self.eat(TokenType.LBRACE)
        
        cases = []
        while self.current_token.type == TokenType.CASE:
            cases.append(self.case_statement())
        
        self.eat(TokenType.RBRACE)
        
        return ClinicalPathStatement(expression, cases)
    
    def case_statement(self):
        """
        case_statement : 'case' expression ':' statement
        """
        self.eat(TokenType.CASE)
        
        value = self.expression()
        
        self.eat(TokenType.COLON)
        
        body = self.statement()
        
        return CaseStatement(value, body)
    
    def return_statement(self):
        """
        return_statement : 'return' expression? ';'
        """
        self.eat(TokenType.RETURN)
        
        value = None
        if self.current_token.type != TokenType.SEMICOLON:
            value = self.expression()
        
        self.eat(TokenType.SEMICOLON)
        
        return ReturnStatement(value)
    
    def prescribe_statement(self):
        """
        prescribe_statement : 'prescribe' '(' prescription_arguments ')' ';'
        """
        self.eat(TokenType.PRESCRIBE)
        
        self.eat(TokenType.LPAREN)
        
        # Assumindo que a ordem é patient, medication, dose [, instructions [, duration]]
        patient = self.expression()
        
        self.eat(TokenType.COMMA)
        
        medication = self.expression()
        
        self.eat(TokenType.COMMA)
        
        dose = self.expression()
        
        instructions = None
        if self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            instructions = self.expression()
        
        duration = None
        if self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            duration = self.expression()
        
        self.eat(TokenType.RPAREN)
        self.eat(TokenType.SEMICOLON)
        
        return PrescribeStatement(patient, medication, dose, instructions, duration)
    
    def expression_statement(self):
        """
        expression_statement : expression ';'
        """
        expr = self.expression()
        
        self.eat(TokenType.SEMICOLON)
        
        return ExpressionStatement(expr)
    
    def expression(self):
        """
        expression : assignment_expression
        """
        return self.assignment_expression()
    
    def assignment_expression(self):
        """
        assignment_expression : logical_or_expression ('=' assignment_expression)?
        """
        expr = self.logical_or_expression()
        
        if self.current_token.type == TokenType.ASSIGN:
            self.eat(TokenType.ASSIGN)
            right = self.assignment_expression()
            expr = BinaryOperation(expr, '=', right)
        
        return expr
    
    def logical_or_expression(self):
        """
        logical_or_expression : logical_and_expression ('||' logical_and_expression)*
        """
        expr = self.logical_and_expression()
        
        while self.current_token.type == TokenType.OR:
            operator = self.current_token.value
            self.eat(TokenType.OR)
            right = self.logical_and_expression()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def logical_and_expression(self):
        """
        logical_and_expression : equality_expression ('&&' equality_expression)*
        """
        expr = self.equality_expression()
        
        while self.current_token.type == TokenType.AND:
            operator = self.current_token.value
            self.eat(TokenType.AND)
            right = self.equality_expression()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def equality_expression(self):
        """
        equality_expression : relational_expression (('==' | '!=') relational_expression)*
        """
        expr = self.relational_expression()
        
        while (self.current_token.type == TokenType.EQ or
               self.current_token.type == TokenType.NEQ):
            operator = self.current_token.value
            self.eat(self.current_token.type)
            right = self.relational_expression()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def relational_expression(self):
        """
        relational_expression : additive_expression (('<' | '>' | '<=' | '>=') additive_expression)*
        """
        expr = self.additive_expression()
        
        while (self.current_token.type == TokenType.LT or
               self.current_token.type == TokenType.GT or
               self.current_token.type == TokenType.LTE or
               self.current_token.type == TokenType.GTE):
            operator = self.current_token.value
            self.eat(self.current_token.type)
            right = self.additive_expression()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def additive_expression(self):
        """
        additive_expression : multiplicative_expression (('+' | '-') multiplicative_expression)*
        """
        expr = self.multiplicative_expression()
        
        while (self.current_token.type == TokenType.PLUS or
               self.current_token.type == TokenType.MINUS):
            operator = self.current_token.value
            self.eat(self.current_token.type)
            right = self.multiplicative_expression()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def multiplicative_expression(self):
        """
        multiplicative_expression : unary_expression (('*' | '/') unary_expression)*
        """
        expr = self.unary_expression()
        
        while (self.current_token.type == TokenType.TIMES or
               self.current_token.type == TokenType.DIVIDE):
            operator = self.current_token.value
            self.eat(self.current_token.type)
            right = self.unary_expression()
            expr = BinaryOperation(expr, operator, right)
        
        return expr
    
    def unary_expression(self):
        """
        unary_expression : ('!' | '-') unary_expression
                         | postfix_expression
        """
        if (self.current_token.type == TokenType.NOT or 
            self.current_token.type == TokenType.MINUS):
            operator = self.current_token.value
            self.eat(self.current_token.type)
            operand = self.unary_expression()
            return UnaryOperation(operator, operand)
        
        return self.postfix_expression()
    
    def postfix_expression(self):
        """
        postfix_expression : primary_expression ('.' identifier ('(' argument_list ')')?)*
        """
        expr = self.primary_expression()
        
        while self.current_token.type == TokenType.DOT:
            self.eat(TokenType.DOT)
            
            if self.current_token.type != TokenType.IDENTIFIER:
                self.error("Esperado identificador após '.'")
            
            property_name = self.current_token.value
            self.eat(TokenType.IDENTIFIER)
            
            # Se for uma chamada de método
            if self.current_token.type == TokenType.LPAREN:
                self.eat(TokenType.LPAREN)
                arguments = self.argument_list()
                self.eat(TokenType.RPAREN)
                
                expr = MethodCall(expr, property_name, arguments)
            else:
                # Senão, é um acesso a propriedade
                expr = PropertyAccess(expr, property_name)
        
        return expr
    
    def primary_expression(self):
        """
        primary_expression : literal
                           | identifier
                           | array_literal
                           | object_literal
                           | '(' expression ')'
                           | function_call
        """
        if self.current_token.type == TokenType.NUMBER:
            value = self.current_token.value
            self.eat(TokenType.NUMBER)
            return Literal(value, "number")
        
        elif self.current_token.type == TokenType.STRING:
            value = self.current_token.value
            self.eat(TokenType.STRING)
            return Literal(value, "string")
        
        elif self.current_token.type == TokenType.DATE:
            value = self.current_token.value
            self.eat(TokenType.DATE)
            return Literal(value, "date")
        
        elif self.current_token.type == TokenType.MEASUREMENT:
            value = self.current_token.value
            self.eat(TokenType.MEASUREMENT)
            return Literal(value, "measurement")
        
        elif self.current_token.type == TokenType.LBRACKET:
            return self.array_literal()
        
        elif self.current_token.type == TokenType.LBRACE:
            return self.object_literal()
        
        elif self.current_token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            expr = self.expression()
            self.eat(TokenType.RPAREN)
            return expr
        
        elif self.current_token.type == TokenType.IDENTIFIER:
            # Verifica se é uma chamada de função ou referência a variável
            if self.peek().type == TokenType.LPAREN:
                return self.function_call()
            else:
                name = self.current_token.value
                self.eat(TokenType.IDENTIFIER)
                return VariableReference(name)
        
        else:
            self.error(f"Expressão primária inesperada: {self.current_token.type}")
    
    def array_literal(self):
        """
        array_literal : '[' (expression (',' expression)*)? ','? ']'
        """
        self.eat(TokenType.LBRACKET)
        
        elements = []
        
        if self.current_token.type != TokenType.RBRACKET:
            elements.append(self.expression())
            
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                
                # Permite uma vírgula final (trailing comma)
                if self.current_token.type == TokenType.RBRACKET:
                    break
                
                elements.append(self.expression())
        
        self.eat(TokenType.RBRACKET)
        
        return ArrayLiteral(elements)
    
    def object_literal(self):
        """
        object_literal : '{' property_list '}'
        """
        self.eat(TokenType.LBRACE)
        
        properties = self.property_list()
        
        self.eat(TokenType.RBRACE)
        
        return ObjectLiteral(properties)
    
    def function_call(self):
        """
        function_call : identifier '(' argument_list ')'
        """
        function_name = self.current_token.value
        self.eat(TokenType.IDENTIFIER)
        
        self.eat(TokenType.LPAREN)
        arguments = self.argument_list()
        self.eat(TokenType.RPAREN)
        
        return FunctionCall(function_name, arguments)
    
    def argument_list(self):
        """
        argument_list : (expression (',' expression)*)?
        """
        arguments = []
        
        if self.current_token.type != TokenType.RPAREN:
            arguments.append(self.expression())
            
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                arguments.append(self.expression())
        
        return arguments


#################################################
# PARTE 3: ANÁLISE SEMÂNTICA
#################################################

class Symbol:
    def __init__(self, name, type=None):
        self.name = name
        self.type = type

class VariableSymbol(Symbol):
    def __init__(self, name, type=None):
        super().__init__(name, type)

class FunctionSymbol(Symbol):
    def __init__(self, name, parameters=None, return_type=None):
        super().__init__(name)
        self.parameters = parameters or []
        self.return_type = return_type

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
    
    def define(self, symbol):
        self.symbols[symbol.name] = symbol
    
    def lookup(self, name):
        symbol = self.symbols.get(name)
        if symbol is not None:
            return symbol
        
        if self.parent is not None:
            return self.parent.lookup(name)
        
        return None
    
    def lookup_local(self, name):
        return self.symbols.get(name)

class SemanticAnalyzer:
    def __init__(self):
        self.current_scope = None
        self.errors = []
    
    def error(self, message, node=None):
        self.errors.append(message)
    
    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        pass
    
    def visit_Program(self, node):
        # Cria o escopo global
        global_scope = SymbolTable()
        self.current_scope = global_scope
        
        # Adiciona as funções da biblioteca padrão
        self.define_builtin_functions(global_scope)
        
        # Visita todas as declarações do programa
        for declaration in node.declarations:
            self.visit(declaration)
        
        return self.errors
    
    def define_builtin_functions(self, scope):
        # Funções integradas na linguagem Charcot
        verify_interaction = FunctionSymbol(
            "verify_interaction",
            [
                VariableSymbol("current_medications", "array"),
                VariableSymbol("drug", "Medication")
            ]
        )
        
        verify_allergies = FunctionSymbol(
            "verify_allergies",
            [
                VariableSymbol("allergies", "array"),
                VariableSymbol("drug", "Medication")
            ]
        )
        
        verify_dosage = FunctionSymbol(
            "verify_dosage",
            [
                VariableSymbol("patient", "Patient"),
                VariableSymbol("drug", "Medication"),
                VariableSymbol("amount", "measurement")
            ]
        )
        
        prescribe = FunctionSymbol(
            "prescribe",
            [
                VariableSymbol("patient", "Patient"),
                VariableSymbol("drug", "string"),
                VariableSymbol("dose", "measurement"),
                VariableSymbol("instructions", "string")
            ],
            "Prescription"
        )
        
        # Adiciona as funções ao escopo global
        scope.define(verify_interaction)
        scope.define(verify_allergies)
        scope.define(verify_dosage)
        scope.define(prescribe)
    
    def visit_ImportDeclaration(self, node):
        # Aqui seria implementada a lógica para importar símbolos de outros módulos
        # Simplificando, apenas registramos a tentativa de importação
        pass
    
    def visit_VariableDeclaration(self, node):
        name = node.name
        
        # Verifica se a variável já está definida no escopo local
        if self.current_scope.lookup_local(name) is not None:
            self.error(f"Variável '{name}' já definida neste escopo")
            return
        
        # Cria e registra o símbolo da variável
        variable_symbol = VariableSymbol(name, node.type_name)
        self.current_scope.define(variable_symbol)
        
        # Visita a expressão de inicialização, se houver
        if node.value is not None:
            self.visit(node.value)
    
    def visit_PatientDeclaration(self, node):
        name = node.name
        
        # Verifica se o paciente já está definido no escopo local
        if self.current_scope.lookup_local(name) is not None:
            self.error(f"Paciente '{name}' já definido neste escopo")
            return
        
        # Cria e registra o símbolo do paciente (como uma variável do tipo Patient)
        patient_symbol = VariableSymbol(name, "Patient")
        self.current_scope.define(patient_symbol)
        
        # Visita as propriedades do paciente
        for prop in node.properties:
            self.visit(prop)
    
    def visit_ProcedureDeclaration(self, node):
        name = node.name
        
        # Verifica se já existe um procedimento com esse nome
        if self.current_scope.lookup_local(name) is not None:
            self.error(f"Procedimento '{name}' já definido neste escopo")
            return
        
        # Cria o símbolo do procedimento (sem tipo de retorno, pois é void)
        param_symbols = []
        for param in node.parameters:
            param_symbols.append(VariableSymbol(param.name, param.type_name))
        
        procedure_symbol = FunctionSymbol(name, param_symbols)
        self.current_scope.define(procedure_symbol)
        
        # Cria um novo escopo para o corpo do procedimento
        procedure_scope = SymbolTable(self.current_scope)
        old_scope = self.current_scope
        self.current_scope = procedure_scope
        
        # Define os parâmetros no escopo do procedimento
        for param in node.parameters:
            self.visit_Parameter(param)
        
        # Visita o corpo do procedimento
        self.visit(node.body)
        
        # Restaura o escopo anterior
        self.current_scope = old_scope
    
    def visit_TreatmentDeclaration(self, node):
        # Tratamentos são similares a procedimentos
        self.visit_ProcedureDeclaration(node)
    
    def visit_Parameter(self, node):
        name = node.name
        
        # Verifica se já existe um parâmetro com esse nome
        if self.current_scope.lookup_local(name) is not None:
            self.error(f"Parâmetro '{name}' já definido neste escopo")
            return
        
        # Cria e registra o símbolo do parâmetro
        param_symbol = VariableSymbol(name, node.type_name)
        self.current_scope.define(param_symbol)
    
    def visit_BlockStatement(self, node):
        # Cria um novo escopo para o bloco
        block_scope = SymbolTable(self.current_scope)
        old_scope = self.current_scope
        self.current_scope = block_scope
        
        # Visita todas as declarações no bloco
        for statement in node.statements:
            self.visit(statement)
        
        # Restaura o escopo anterior
        self.current_scope = old_scope
    
    def visit_IfStatement(self, node):
        # Visita a condição
        self.visit(node.condition)
        
        # Visita o corpo do if
        self.visit(node.if_body)
        
        # Visita o corpo do else, se houver
        if node.else_body is not None:
            self.visit(node.else_body)
    
    def visit_WhileStatement(self, node):
        # Visita a condição
        self.visit(node.condition)
        
        # Visita o corpo do loop
        self.visit(node.body)
    
    def visit_ForEachStatement(self, node):
        # Cria um novo escopo para o loop
        loop_scope = SymbolTable(self.current_scope)
        old_scope = self.current_scope
        self.current_scope = loop_scope
        
        # Visita a variável de iteração
        self.visit(node.variable)
        
        # Visita a coleção
        self.visit(node.collection)
        
        # Visita o corpo do loop
        self.visit(node.body)
        
        # Restaura o escopo anterior
        self.current_scope = old_scope
    
    def visit_ClinicalPathStatement(self, node):
        # Visita a expressão do switch
        self.visit(node.expression)
        
        # Visita todos os casos
        for case in node.cases:
            self.visit(case)
    
    def visit_CaseStatement(self, node):
        # Visita o valor do caso
        self.visit(node.value)
        
        # Visita o corpo do caso
        self.visit(node.body)
    
    def visit_ReturnStatement(self, node):
        # Visita a expressão de retorno, se houver
        if node.value is not None:
            self.visit(node.value)
    
    def visit_ExpressionStatement(self, node):
        # Visita a expressão
        self.visit(node.expression)
    
    def visit_PrescribeStatement(self, node):
        # Visita todos os argumentos da prescrição
        self.visit(node.patient)
        self.visit(node.medication)
        self.visit(node.dose)
        
        if node.instructions is not None:
            self.visit(node.instructions)
        
        if node.duration is not None:
            self.visit(node.duration)
    
    def visit_BinaryOperation(self, node):
        # Visita as expressões à esquerda e à direita
        self.visit(node.left)
        self.visit(node.right)
    
    def visit_UnaryOperation(self, node):
        # Visita o operando
        self.visit(node.operand)
    
    def visit_VariableReference(self, node):
        name = node.name
        
        # Verifica se a variável está definida
        symbol = self.current_scope.lookup(name)
        if symbol is None:
            self.error(f"Variável '{name}' não definida")
    
    def visit_PropertyAccess(self, node):
        # Visita a expressão do objeto
        self.visit(node.object_expr)
        
        # Aqui seria verificado se a propriedade existe no tipo do objeto
        # Mas isso requereria um sistema de tipos mais complexo
    
    def visit_FunctionCall(self, node):
        name = node.name
        
        # Verifica se a função está definida
        symbol = self.current_scope.lookup(name)
        if symbol is None or not isinstance(symbol, FunctionSymbol):
            self.error(f"Função '{name}' não definida")
            return
        
        # Visita todos os argumentos
        for arg in node.arguments:
            self.visit(arg)
        
        # Verifica se o número de argumentos está correto
        if len(node.arguments) != len(symbol.parameters):
            self.error(
                f"Número incorreto de argumentos para '{name}'. " +
                f"Esperado {len(symbol.parameters)}, mas recebeu {len(node.arguments)}"
            )
    
    def visit_MethodCall(self, node):
        # Visita a expressão do objeto
        self.visit(node.object_expr)
        
        # Visita todos os argumentos
        for arg in node.arguments:
            self.visit(arg)
        
        # Aqui seria verificado se o método existe no tipo do objeto
        # Mas isso requereria um sistema de tipos mais complexo
    
    def visit_Literal(self, node):
        # Nada a verificar em literais
        pass
    
    def visit_ArrayLiteral(self, node):
        # Visita todos os elementos do array
        for element in node.elements:
            self.visit(element)
    
    def visit_ObjectLiteral(self, node):
        # Visita todas as propriedades do objeto
        for prop in node.properties:
            self.visit(prop)
    
    def visit_PropertyAssignment(self, node):
        # Visita o valor da propriedade
        self.visit(node.value)


#################################################
# PARTE 4: GERAÇÃO DE CÓDIGO LLVM IR
#################################################

class LLVMCodeGenerator:
    def __init__(self):
        # Isso seria implementado com a biblioteca LLVM
        # Para simplificar, vamos apenas construir strings LLVM IR
        self.buffer = []
        self.indentation = 0
        self.label_counter = 0
        self.temp_counter = 0
        self.vars = {}  # Mapeamento de variáveis para registradores
    
    def indent(self):
        self.indentation += 2
    
    def dedent(self):
        self.indentation -= 2
    
    def emit(self, code):
        self.buffer.append(' ' * self.indentation + code)
    
    def get_code(self):
        return '\n'.join(self.buffer)
    
    def fresh_label(self):
        """Gera um rótulo único."""
        label = f"label{self.label_counter}"
        self.label_counter += 1
        return label
    
    def fresh_temp(self):
        """Gera um registrador temporário único."""
        temp = f"%t{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def get_type_str(self, type_name):
        """Converte um tipo Charcot para um tipo LLVM IR."""
        type_mapping = {
            "int": "i32",
            "float": "float",
            "string": "i8*",
            "bool": "i1",
            "date": "i32",  # Representado como timestamp Unix
            "measurement": "float",  # Simplificado
            "Patient": "%Patient*",
            "Medication": "%Medication*",
            "Prescription": "%Prescription*"
        }
        
        return type_mapping.get(type_name, "i8*")  # Padrão para tipos desconhecidos
    
    def generate(self, ast):
        """Gera código LLVM IR a partir da AST."""
        # Emite os cabeçalhos e declarações globais
        self.generate_prelude()
        
        # Visita o nó raiz (Program)
        self.visit(ast)
        
        return self.get_code()
    
    def generate_prelude(self):
        """Gera as declarações iniciais e tipos necessários."""
        # Declarações de tipo para estruturas médicas
        self.emit("; Tipos médicos personalizados")
        
        # Tipo Patient
        self.emit("%Patient = type {")
        self.indent()
        self.emit("i8*,   ; id")
        self.emit("i8*,   ; name")
        self.emit("i32,   ; birth (timestamp)")
        self.emit("float, ; weight em kg")
        self.emit("float, ; height em cm")
        self.emit("i8**   ; allergies (array de strings)")
        self.dedent()
        self.emit("}")
        self.emit("")
        
        # Tipo Medication
        self.emit("%Medication = type {")
        self.indent()
        self.emit("i8*,   ; name")
        self.emit("i8*,   ; active_ingredient")
        self.emit("float, ; strength")
        self.emit("i8*    ; unit (mg, ml, etc)")
        self.dedent()
        self.emit("}")
        self.emit("")
        
        # Tipo Prescription
        self.emit("%Prescription = type {")
        self.indent()
        self.emit("%Patient*,    ; patient")
        self.emit("%Medication*, ; medication")
        self.emit("float,        ; dose")
        self.emit("i8*,          ; instructions")
        self.emit("i32,          ; valid_for (dias)")
        self.emit("i32,          ; renewals")
        self.emit("i8*,          ; prescribed_by")
        self.emit("i32           ; date (timestamp)")
        self.dedent()
        self.emit("}")
        self.emit("")
        
        # Funções de biblioteca padrão
        self.emit("; Funções de biblioteca padrão")
        
        # Função verify_interaction
        self.emit("declare i1 @verify_interaction(i8**, %Medication*)")
        
        # Função verify_allergies
        self.emit("declare i1 @verify_allergies(i8**, %Medication*)")
        
        # Função verify_dosage
        self.emit("declare i1 @verify_dosage(%Patient*, %Medication*, float)")
        
        # Função log_administration
        self.emit("declare void @log_administration(%Patient*, %Medication*, float, i32)")
        
        # Outras funções de utilidade
        self.emit("declare i8* @string_concat(i8*, i8*)")
        self.emit("declare i32 @get_current_timestamp()")
        self.emit("declare %Medication* @get_medication_by_name(i8*)")
        self.emit("")
    
    def visit(self, node):
        """Visita um nó da AST e gera o código correspondente."""
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        """Método genérico para nós não implementados explicitamente."""
        print(f"Warning: No visit method for {type(node).__name__}")
        return None
    
    def visit_Program(self, node):
        """Visita o nó raiz do programa."""
        # Gera código para todas as declarações
        for decl in node.declarations:
            self.visit(decl)
    
    def visit_ImportDeclaration(self, node):
        """Importações são resolvidas pelo analisador semântico, não gera código LLVM."""
        self.emit(f"; Importação: {node.module_name}")
    
    def visit_VariableDeclaration(self, node):
        """Gera código para declaração de variável."""
        # No escopo global, declaramos variáveis globais
        # No escopo local, usamos alloca
        var_name = node.name
        
        # Determina o tipo LLVM da variável
        if node.type_name:
            llvm_type = self.get_type_str(node.type_name)
        else:
            # Inferência de tipo simples baseada no valor, se disponível
            if node.value:
                # Aqui seria implementada a inferência completa
                llvm_type = "i8*"  # Assumindo string como padrão
            else:
                llvm_type = "i8*"  # Tipo padrão para variáveis sem tipo e sem valor
        
        # Aloca memória para a variável
        temp = self.fresh_temp()
        self.emit(f"{temp} = alloca {llvm_type}")
        
        # Registra a variável para uso posterior
        self.vars[var_name] = (temp, llvm_type)
        
        # Se tiver um valor inicial, atribui-o
        if node.value:
            value_temp = self.visit(node.value)
            if value_temp:
                self.emit(f"store {llvm_type} {value_temp}, {llvm_type}* {temp}")
    
    def visit_PatientDeclaration(self, node):
        """Gera código para declaração de paciente."""
        patient_name = node.name
        
        # Aloca memória para a estrutura Patient
        temp = self.fresh_temp()
        self.emit(f"{temp} = alloca %Patient")
        
        # Registra o paciente para uso posterior
        self.vars[patient_name] = (temp, "%Patient*")
        
        # Inicializa os campos do paciente com base nas propriedades fornecidas
        for prop in node.properties:
            prop_name = prop.name
            prop_value_temp = self.visit(prop.value)
            
            # Obtém o campo correto com base no nome da propriedade
            field_index = {
                "id": 0,
                "name": 1,
                "birth": 2,
                "weight": 3,
                "height": 4,
                "allergies": 5
            }.get(prop_name, -1)
            
            if field_index >= 0:
                # Acessa o campo
                field_ptr_temp = self.fresh_temp()
                self.emit(f"{field_ptr_temp} = getelementptr %Patient, %Patient* {temp}, i32 0, i32 {                field_index}")
                
                # Determina o tipo do campo
                field_type = [
                    "i8*",   # id
                    "i8*",   # name
                    "i32",   # birth
                    "float", # weight
                    "float", # height
                    "i8**"   # allergies
                ][field_index]
                
                # Armazena o valor
                self.emit(f"store {field_type} {prop_value_temp}, {field_type}* {field_ptr_temp}")
        
        return obj_temp


#################################################
# PARTE 5: OTIMIZAÇÃO
#################################################

class Optimizer:
    """
    Realiza otimizações no código LLVM IR gerado.
    """
    def __init__(self, llvm_code):
        self.llvm_code = llvm_code
    
    def optimize(self):
        """Aplica várias otimizações no código LLVM."""
        self.llvm_code = self.constant_folding(self.llvm_code)
        self.llvm_code = self.dead_code_elimination(self.llvm_code)
        self.llvm_code = self.common_subexpression_elimination(self.llvm_code)
        return self.llvm_code
    
    def constant_folding(self, code):
        """
        Dobramento de constantes: substitui expressões constantes
        por seus valores calculados em tempo de compilação.
        """
        # Implementação simplificada
        return code
    
    def dead_code_elimination(self, code):
        """
        Eliminação de código morto: remove instruções que não
        afetam o resultado do programa.
        """
        # Implementação simplificada
        return code
    
    def common_subexpression_elimination(self, code):
        """
        Eliminação de subexpressões comuns: identifica e elimina
        cálculos redundantes.
        """
        # Implementação simplificada
        return code


#################################################
# PARTE 6: GERAÇÃO DE CÓDIGO NATIVO
#################################################

class NativeCodeGenerator:
    """
    Gera código nativo a partir do código LLVM IR otimizado.
    Normalmente isso seria feito pelo backend LLVM, mas aqui
    apenas simulamos a chamada.
    """
    def __init__(self, llvm_code, target='x86_64'):
        self.llvm_code = llvm_code
        self.target = target
    
    def generate(self, output_file):
        """
        Gera código nativo para o alvo especificado e
        escreve no arquivo de saída.
        """
        # Simula a chamada para o backend LLVM
        print(f"Gerando código nativo para {self.target}...")
        print(f"Escrevendo em {output_file}...")
        
        # Em um cenário real, chamaríamos o LLVM para compilar
        # o código IR para código de máquina
        # Por exemplo: llc -filetype=obj -o output.o input.ll
        
        # Escreve o código LLVM em um arquivo .ll para referência
        llvm_file = output_file.replace('.o', '.ll')
        with open(llvm_file, 'w') as f:
            f.write(self.llvm_code)
        
        print(f"Código LLVM IR escrito em {llvm_file}")
        print("Compilação nativa simulada (requer LLVM real para execução)")


#################################################
# PARTE 7: FRONTEND (LINHA DE COMANDO)
#################################################

def main():
    """Função principal do compilador."""
    parser = argparse.ArgumentParser(description='Compilador da Linguagem Charcot')
    parser.add_argument('input', help='Arquivo de entrada (.charcot)')
    parser.add_argument('-o', '--output', help='Arquivo de saída (.o)')
    parser.add_argument('-S', '--assembly', action='store_true', help='Gerar apenas código LLVM IR')
    parser.add_argument('-v', '--verbose', action='store_true', help='Modo verboso')
    parser.add_argument('--dump-ast', action='store_true', help='Mostrar AST')
    parser.add_argument('--dump-tokens', action='store_true', help='Mostrar tokens')
    parser.add_argument('--no-optimize', action='store_true', help='Desabilitar otimizações')
    parser.add_argument('-t', '--target', default='x86_64', help='Arquitetura alvo (default: x86_64)')
    
    args = parser.parse_args()
    
    input_file = args.input
    output_file = args.output or input_file.replace('.charcot', '.o')
    
    if not input_file.endswith('.charcot'):
        print("Aviso: O arquivo de entrada não tem extensão .charcot")
    
    # Lê o arquivo de entrada
    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo {input_file} não encontrado")
        return 1
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return 1
    
    if args.verbose:
        print(f"Compilando {input_file}...")
    
    try:
        # Fase 1: Análise léxica (Tokenização)
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        
        if args.dump_tokens:
            print("\n--- Tokens ---")
            for token in tokens:
                print(token)
        
        # Fase 2: Análise sintática (Parsing)
        parser = Parser(tokens)
        ast = parser.parse()
        
        if args.dump_ast:
            print("\n--- AST ---")
            print_ast(ast)  # Função para imprimir a AST (não implementada aqui)
        
        # Fase 3: Análise semântica
        semantic_analyzer = SemanticAnalyzer()
        errors = semantic_analyzer.visit(ast)
        
        if errors:
            print("\n--- Erros Semânticos ---")
            for error in errors:
                print(f"Erro: {error}")
            return 1
        
        # Fase 4: Geração de código LLVM IR
        code_generator = LLVMCodeGenerator()
        llvm_code = code_generator.generate(ast)
        
        # Fase 5: Otimização (opcional)
        if not args.no_optimize:
            optimizer = Optimizer(llvm_code)
            llvm_code = optimizer.optimize()
        
        if args.assembly:
            # Apenas gera o código LLVM IR
            output_ll = output_file.replace('.o', '.ll')
            with open(output_ll, 'w') as f:
                f.write(llvm_code)
            
            if args.verbose:
                print(f"Código LLVM IR gerado em {output_ll}")
        else:
            # Fase 6: Geração de código nativo
            native_generator = NativeCodeGenerator(llvm_code, args.target)
            native_generator.generate(output_file)
            
            if args.verbose:
                print(f"Código nativo gerado em {output_file}")
        
        if args.verbose:
            print("Compilação concluída com sucesso!")
        
        return 0
    
    except SyntaxError as e:
        print(f"Erro de sintaxe: {e}")
        return 1
    except Exception as e:
        print(f"Erro durante a compilação: {e}")
        import traceback
        traceback.print_exc()
        return 1


def print_ast(node, indent=0):
    """Função auxiliar para imprimir a AST de forma legível."""
    prefix = '  ' * indent
    
    if isinstance(node, Program):
        print(f"{prefix}Program:")
        for decl in node.declarations:
            print_ast(decl, indent + 1)
    
    elif isinstance(node, ImportDeclaration):
        print(f"{prefix}Import: {node.module_name}")
    
    elif isinstance(node, VariableDeclaration):
        print(f"{prefix}Variable: {node.name} : {node.type_name or 'inferred'}")
        if node.value:
            print_ast(node.value, indent + 1)
    
    elif isinstance(node, PatientDeclaration):
        print(f"{prefix}Patient: {node.name}")
        for prop in node.properties:
            print_ast(prop, indent + 1)
    
    elif isinstance(node, ProcedureDeclaration):
        print(f"{prefix}Procedure: {node.name}")
        print(f"{prefix}  Parameters:")
        for param in node.parameters:
            print_ast(param, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    
    elif isinstance(node, TreatmentDeclaration):
        print(f"{prefix}Treatment: {node.name}")
        print(f"{prefix}  Parameters:")
        for param in node.parameters:
            print_ast(param, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    
    elif isinstance(node, Parameter):
        print(f"{prefix}Param: {node.name} : {node.type_name or 'any'}")
    
    elif isinstance(node, BlockStatement):
        print(f"{prefix}Block:")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)
    
    elif isinstance(node, IfStatement):
        print(f"{prefix}If:")
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Then:")
        print_ast(node.if_body, indent + 2)
        if node.else_body:
            print(f"{prefix}  Else:")
            print_ast(node.else_body, indent + 2)
    
    elif isinstance(node, WhileStatement):
        print(f"{prefix}While:")
        print(f"{prefix}  Condition:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    
    elif isinstance(node, ForEachStatement):
        print(f"{prefix}ForEach:")
        print(f"{prefix}  Variable:")
        print_ast(node.variable, indent + 2)
        print(f"{prefix}  Collection:")
        print_ast(node.collection, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    
    elif isinstance(node, ClinicalPathStatement):
        print(f"{prefix}ClinicalPath:")
        print(f"{prefix}  Expression:")
        print_ast(node.expression, indent + 2)
        print(f"{prefix}  Cases:")
        for case in node.cases:
            print_ast(case, indent + 2)
    
    elif isinstance(node, CaseStatement):
        print(f"{prefix}Case:")
        print(f"{prefix}  Value:")
        print_ast(node.value, indent + 2)
        print(f"{prefix}  Body:")
        print_ast(node.body, indent + 2)
    
    elif isinstance(node, ReturnStatement):
        print(f"{prefix}Return:")
        if node.value:
            print_ast(node.value, indent + 1)
    
    elif isinstance(node, ExpressionStatement):
        print(f"{prefix}Expression:")
        print_ast(node.expression, indent + 1)
    
    elif isinstance(node, PrescribeStatement):
        print(f"{prefix}Prescribe:")
        print(f"{prefix}  Patient:")
        print_ast(node.patient, indent + 2)
        print(f"{prefix}  Medication:")
        print_ast(node.medication, indent + 2)
        print(f"{prefix}  Dose:")
        print_ast(node.dose, indent + 2)
        if node.instructions:
            print(f"{prefix}  Instructions:")
            print_ast(node.instructions, indent + 2)
        if node.duration:
            print(f"{prefix}  Duration:")
            print_ast(node.duration, indent + 2)
    
    elif isinstance(node, BinaryOperation):
        print(f"{prefix}Binary: {node.operator}")
        print(f"{prefix}  Left:")
        print_ast(node.left, indent + 2)
        print(f"{prefix}  Right:")
        print_ast(node.right, indent + 2)
    
    elif isinstance(node, UnaryOperation):
        print(f"{prefix}Unary: {node.operator}")
        print(f"{prefix}  Operand:")
        print_ast(node.operand, indent + 2)
    
    elif isinstance(node, VariableReference):
        print(f"{prefix}Variable: {node.name}")
    
    elif isinstance(node, PropertyAccess):
        print(f"{prefix}Property Access: {node.property_name}")
        print(f"{prefix}  Object:")
        print_ast(node.object_expr, indent + 2)
    
    elif isinstance(node, FunctionCall):
        print(f"{prefix}Function Call: {node.name}")
        print(f"{prefix}  Arguments:")
        for arg in node.arguments:
            print_ast(arg, indent + 2)
    
    elif isinstance(node, MethodCall):
        print(f"{prefix}Method Call: {node.method_name}")
        print(f"{prefix}  Object:")
        print_ast(node.object_expr, indent + 2)
        print(f"{prefix}  Arguments:")
        for arg in node.arguments:
            print_ast(arg, indent + 2)
    
    elif isinstance(node, Literal):
        print(f"{prefix}Literal ({node.literal_type}): {node.value}")
    
    elif isinstance(node, ArrayLiteral):
        print(f"{prefix}Array:")
        for elem in node.elements:
            print_ast(elem, indent + 1)
    
    elif isinstance(node, ObjectLiteral):
        print(f"{prefix}Object:")
        for prop in node.properties:
            print_ast(prop, indent + 1)
    
    elif isinstance(node, PropertyAssignment):
        print(f"{prefix}Property: {node.name} =")
        print_ast(node.value, indent + 1)
    
    else:
        print(f"{prefix}Unknown node type: {type(node).__name__}")


if __name__ == "__main__":
    sys.exit(main())

                
    # Determina o tipo do campo
    field_type = ["i8*", "i8*", "i32", "float", "float", "i8**"][field_index]  # [id, name, birth, weight, height, allergies]                
    # Armazena o valor
    self.emit(f"store {field_type} {prop_value_temp}, {field_type}* {field_ptr_temp}")
    
    def visit_ProcedureDeclaration(self, node):
        """Gera código para declaração de procedimento."""
        proc_name = node.name
        
        # Determina os tipos dos parâmetros
        param_types = []
        for param in node.parameters:
            if param.type_name:
                param_types.append(self.get_type_str(param.type_name))
            else:
                param_types.append("i8*")  # Tipo padrão
        
        # Cria a assinatura da função
        params_str = ", ".join(param_types)
        self.emit(f"define void @{proc_name}({params_str}) {{")
        self.indent()
        
        # Salva o contexto anterior de variáveis e cria um novo
        old_vars = self.vars.copy()
        self.vars = {}
        
        # Aloca memória para os parâmetros e mapeia-os para variáveis locais
        for i, param in enumerate(node.parameters):
            param_name = param.name
            param_type = param_types[i]
            
            # Aloca memória para o parâmetro
            temp = self.fresh_temp()
            self.emit(f"{temp} = alloca {param_type}")
            
            # Armazena o valor do parâmetro
            self.emit(f"store {param_type} %{i}, {param_type}* {temp}")
            
            # Registra o parâmetro para uso posterior
            self.vars[param_name] = (temp, param_type)
        
        # Gera código para o corpo do procedimento
        self.visit(node.body)
        
        # Adiciona return void padrão se não houver return explícito
        self.emit("ret void")
        
        # Restaura o contexto anterior de variáveis
        self.vars = old_vars
        
        self.dedent()
        self.emit("}")
        self.emit("")
    
    def visit_TreatmentDeclaration(self, node):
        """Tratamentos são similares a procedimentos."""
        self.visit_ProcedureDeclaration(node)
    
    def visit_BlockStatement(self, node):
        """Gera código para um bloco de declarações."""
        # Salva o contexto anterior de variáveis (para escopo)
        old_vars = self.vars.copy()
        
        # Gera código para cada declaração no bloco
        for stmt in node.statements:
            self.visit(stmt)
        
        # Restaura o contexto anterior de variáveis
        # Este é um escopo léxico simplificado - variáveis declaradas
        # no bloco não estarão disponíveis fora dele
        self.vars = old_vars
    
    def visit_IfStatement(self, node):
        """Gera código para declaração if/else."""
        # Gera código para a condição
        cond_temp = self.visit(node.condition)
        
        # Cria rótulos para os blocos then, else e continue
        then_label = self.fresh_label()
        else_label = self.fresh_label()
        cont_label = self.fresh_label()
        
        # Branch condicional
        self.emit(f"br i1 {cond_temp}, label %{then_label}, label %{else_label}")
        
        # Bloco 'then'
        self.emit(f"{then_label}:")
        self.visit(node.if_body)
        self.emit(f"br label %{cont_label}")
        
        # Bloco 'else'
        self.emit(f"{else_label}:")
        if node.else_body:
            self.visit(node.else_body)
        self.emit(f"br label %{cont_label}")
        
        # Bloco de continuação
        self.emit(f"{cont_label}:")
    
    def visit_WhileStatement(self, node):
        """Gera código para loop while."""
        # Cria rótulos para os blocos de condição, corpo e saída
        cond_label = self.fresh_label()
        body_label = self.fresh_label()
        exit_label = self.fresh_label()
        
        # Branch para a condição
        self.emit(f"br label %{cond_label}")
        
        # Bloco de condição
        self.emit(f"{cond_label}:")
        cond_temp = self.visit(node.condition)
        self.emit(f"br i1 {cond_temp}, label %{body_label}, label %{exit_label}")
        
        # Bloco do corpo
        self.emit(f"{body_label}:")
        self.visit(node.body)
        self.emit(f"br label %{cond_label}")
        
        # Bloco de saída
        self.emit(f"{exit_label}:")
    
    def visit_ForEachStatement(self, node):
        """Gera código para loop foreach."""
        # Esta é uma implementação simplificada para arrays
        # Uma implementação completa precisaria suportar diferentes tipos de coleções
        
        # Gera código para a coleção
        collection_temp = self.visit(node.collection)
        
        # Obtém o tamanho da coleção (assumindo que é um array)
        size_temp = self.fresh_temp()
        self.emit(f"{size_temp} = call i32 @array_size(i8** {collection_temp})")
        
        # Inicializa o índice
        index_temp = self.fresh_temp()
        self.emit(f"{index_temp} = alloca i32")
        self.emit(f"store i32 0, i32* {index_temp}")
        
        # Cria rótulos para os blocos de condição, corpo e saída
        cond_label = self.fresh_label()
        body_label = self.fresh_label()
        exit_label = self.fresh_label()
        
        # Branch para a condição
        self.emit(f"br label %{cond_label}")
        
        # Bloco de condição
        self.emit(f"{cond_label}:")
        current_index_temp = self.fresh_temp()
        self.emit(f"{current_index_temp} = load i32, i32* {index_temp}")
        
        cond_temp = self.fresh_temp()
        self.emit(f"{cond_temp} = icmp slt i32 {current_index_temp}, {size_temp}")
        self.emit(f"br i1 {cond_temp}, label %{body_label}, label %{exit_label}")
        
        # Bloco do corpo
        self.emit(f"{body_label}:")
        
        # Obtém o elemento atual
        element_temp = self.fresh_temp()
        self.emit(f"{element_temp} = call i8* @array_get(i8** {collection_temp}, i32 {current_index_temp})")
        
        # Se node.variable for uma declaração de variável, declaramos a variável
        # Senão, assumimos que é uma referência a uma variável existente
        if isinstance(node.variable, VariableDeclaration):
            var_name = node.variable.name
            var_type = self.get_type_str(node.variable.type_name) if node.variable.type_name else "i8*"
            
            var_temp = self.fresh_temp()
            self.emit(f"{var_temp} = alloca {var_type}")
            self.emit(f"store {var_type} {element_temp}, {var_type}* {var_temp}")
            
            self.vars[var_name] = (var_temp, var_type)
        else:
            var_name = node.variable.name
            var_temp, var_type = self.vars.get(var_name, (None, "i8*"))
            
            if var_temp:
                self.emit(f"store {var_type} {element_temp}, {var_type}* {var_temp}")
        
        # Visita o corpo do loop
        self.visit(node.body)
        
        # Incrementa o índice
        self.emit(f"{current_index_temp} = add i32 {current_index_temp}, 1")
        self.emit(f"store i32 {current_index_temp}, i32* {index_temp}")
        
        # Volta para a condição
        self.emit(f"br label %{cond_label}")
        
        # Bloco de saída
        self.emit(f"{exit_label}:")
    
    def visit_ClinicalPathStatement(self, node):
        """Gera código para declaração clinical_path (switch/case)."""
        # Gera código para a expressão
        expr_temp = self.visit(node.expression)
        
        # Cria um rótulo para o bloco de saída
        exit_label = self.fresh_label()
        
        # Gera código para cada caso
        case_labels = []
        for case in node.cases:
            case_labels.append(self.fresh_label())
        
        # Para cada caso, compara com a expressão
        for i, case in enumerate(node.cases):
            case_value_temp = self.visit(case.value)
            
            # Compara o valor do caso com a expressão
            cmp_temp = self.fresh_temp()
            self.emit(f"{cmp_temp} = call i1 @values_equal(i8* {expr_temp}, i8* {case_value_temp})")
            
            # Se for igual, vai para o bloco do caso
            next_label = self.fresh_label() if i < len(node.cases) - 1 else exit_label
            self.emit(f"br i1 {cmp_temp}, label %{case_labels[i]}, label %{next_label}")
            
            # Bloco do caso
            self.emit(f"{case_labels[i]}:")
            self.visit(case.body)
            self.emit(f"br label %{exit_label}")
            
            if i < len(node.cases) - 1:
                self.emit(f"{next_label}:")
        
        # Bloco de saída
        self.emit(f"{exit_label}:")
    
    def visit_ReturnStatement(self, node):
        """Gera código para declaração return."""
        if node.value:
            value_temp = self.visit(node.value)
            # O tipo de retorno dependeria do contexto da função
            # Para simplificar, assumimos que os procedimentos são void
            self.emit(f"ret void")
        else:
            self.emit("ret void")
    
    def visit_ExpressionStatement(self, node):
        """Gera código para uma declaração de expressão."""
        self.visit(node.expression)
    
    def visit_PrescribeStatement(self, node):
        """Gera código para declaração prescribe."""
        # Gera código para os argumentos
        patient_temp = self.visit(node.patient)
        medication_temp = self.visit(node.medication)
        dose_temp = self.visit(node.dose)
        
        instructions_temp = None
        if node.instructions:
            instructions_temp = self.visit(node.instructions)
        else:
            # String vazia como padrão
            instructions_temp = '""'
        
        duration_temp = None
        if node.duration:
            duration_temp = self.visit(node.duration)
        else:
            # Duração padrão (30 dias)
            duration_temp = "30"
        
        # Chama a função de prescrição
        self.emit(f"call void @prescribe(%Patient* {patient_temp}, %Medication* {medication_temp}, float {dose_temp}, i8* {instructions_temp}, i32 {duration_temp})")
    
    def visit_BinaryOperation(self, node):
        """Gera código para operações binárias."""
        left_temp = self.visit(node.left)
        right_temp = self.visit(node.right)
        
        result_temp = self.fresh_temp()
        
        # Tipo de operação
        if node.operator in ['+', '-', '*', '/']:
            # Operações aritméticas
            op_map = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'fdiv'}
            self.emit(f"{result_temp} = {op_map[node.operator]} float {left_temp}, {right_temp}")
        
        elif node.operator in ['>', '<', '>=', '<=', '==', '!=']:
            # Operações de comparação
            op_map = {'>': 'sgt', '<': 'slt', '>=': 'sge', '<=': 'sle', '==': 'eq', '!=': 'ne'}
            self.emit(f"{result_temp} = fcmp {op_map[node.operator]} float {left_temp}, {right_temp}")
        
        elif node.operator in ['&&', '||']:
            # Operações lógicas
            if node.operator == '&&':
                # a && b => a ? b : false
                temp1 = self.fresh_temp()
                label1 = self.fresh_label()
                label2 = self.fresh_label()
                label3 = self.fresh_label()
                
                self.emit(f"br i1 {left_temp}, label %{label1}, label %{label2}")
                self.emit(f"{label1}:")
                self.emit(f"{temp1} = {right_temp}")
                self.emit(f"br label %{label3}")
                self.emit(f"{label2}:")
                self.emit(f"{temp1} = false")
                self.emit(f"br label %{label3}")
                self.emit(f"{label3}:")
                self.emit(f"{result_temp} = phi i1 [ {temp1}, %{label1} ], [ false, %{label2} ]")
            
            else:  # '||'
                # a || b => a ? true : b
                temp1 = self.fresh_temp()
                label1 = self.fresh_label()
                label2 = self.fresh_label()
                label3 = self.fresh_label()
                
                self.emit(f"br i1 {left_temp}, label %{label1}, label %{label2}")
                self.emit(f"{label1}:")
                self.emit(f"{temp1} = true")
                self.emit(f"br label %{label3}")
                self.emit(f"{label2}:")
                self.emit(f"{temp1} = {right_temp}")
                self.emit(f"br label %{label3}")
                self.emit(f"{label3}:")
                self.emit(f"{result_temp} = phi i1 [ true, %{label1} ], [ {temp1}, %{label2} ]")
        
        elif node.operator == '=':
            # Atribuição
            # Assumindo que left_temp é um ponteiro para o lado esquerdo
            self.emit(f"store float {right_temp}, float* {left_temp}")
            result_temp = right_temp
        
        return result_temp
    
    def visit_UnaryOperation(self, node):
        """Gera código para operações unárias."""
        operand_temp = self.visit(node.operand)
        
        result_temp = self.fresh_temp()
        
        if node.operator == '-':
            self.emit(f"{result_temp} = fneg float {operand_temp}")
        elif node.operator == '!':
            self.emit(f"{result_temp} = xor i1 {operand_temp}, true")
        
        return result_temp
    
    def visit_VariableReference(self, node):
        """Gera código para referência a variável."""
        var_name = node.name
        
        if var_name in self.vars:
            var_temp, var_type = self.vars[var_name]
            
            # Carrega o valor da variável
            result_temp = self.fresh_temp()
            self.emit(f"{result_temp} = load {var_type}, {var_type}* {var_temp}")
            
            return result_temp
        else:
            print(f"Warning: Variable {var_name} not found")
            return "null"
    
    def visit_PropertyAccess(self, node):
        """Gera código para acesso a propriedade."""
        obj_temp = self.visit(node.object_expr)
        prop_name = node.property_name
        
        # Aqui seria necessário conhecer o tipo do objeto para
        # determinar o índice correto do campo
        # Para simplificar, assumimos que é um paciente
        
        field_index = {
            "id": 0,
            "name": 1,
            "birth": 2,
            "weight": 3,
            "height": 4,
            "allergies": 5
        }.get(prop_name, -1)
        
        if field_index >= 0:
            # Acessa o campo
            field_ptr_temp = self.fresh_temp()
            self.emit(f"{field_ptr_temp} = getelementptr %Patient, %Patient* {obj_temp}, i32 0, i32 {field_index}")
            
            # Determina o tipo do campo
            field_type = [
                "i8*",   # id
                "i8*",   # name
                "i32",   # birth
                "float", # weight
                "float", # height
                "i8**"   # allergies
            ][field_index]
            
            # Carrega o valor do campo
            result_temp = self.fresh_temp()
            self.emit(f"{result_temp} = load {field_type}, {field_type}* {field_ptr_temp}")
            
            return result_temp
        else:
            print(f"Warning: Property {prop_name} not found")
            return "null"
    
    def visit_FunctionCall(self, node):
        """Gera código para chamada de função."""
        # Gera código para os argumentos
        arg_temps = []
        for arg in node.arguments:
            arg_temp = self.visit(arg)
            arg_temps.append(arg_temp)
        
        # Chama a função
        result_temp = self.fresh_temp()
        
        # O tipo de retorno depende da função
        # Para simplificar, assumimos void
        func_name = node.name
        arg_types_str = ", ".join(["i8*"] * len(arg_temps))  # Assumindo i8* para todos os argumentos
        args_str = ", ".join([f"i8* {arg}" for arg in arg_temps])
        
        self.emit(f"{result_temp} = call i8* @{func_name}({args_str})")
        
        return result_temp
    
    def visit_MethodCall(self, node):
        """Gera código para chamada de método."""
        # Similar à chamada de função, mas com o objeto como primeiro argumento
        obj_temp = self.visit(node.object_expr)
        
        # Gera código para os argumentos
        arg_temps = [obj_temp]  # O objeto é o primeiro argumento
        for arg in node.arguments:
            arg_temp = self.visit(arg)
            arg_temps.append(arg_temp)
        
        # Chama o método
        result_temp = self.fresh_temp()
        
        # O nome do método é prefixado com o tipo do objeto
        # Para simplificar, assumimos que é um paciente
        method_name = f"Patient_{node.method_name}"
        
        # Tipos e argumentos
        arg_types = ["i8*"] * len(arg_temps)  # Assumindo i8* para todos os argumentos
        arg_types_str = ", ".join(arg_types)
        args_str = ", ".join([f"{t} {a}" for t, a in zip(arg_types, arg_temps)])
        
        self.emit(f"{result_temp} = call i8* @{method_name}({args_str})")
        
        return result_temp
    
    def visit_Literal(self, node):
        """Gera código para literais."""
        literal_type = node.literal_type
        value = node.value
        
        result_temp = self.fresh_temp()
        
        if literal_type == "number":
            # Números são tratados como float para simplificar
            self.emit(f"{result_temp} = {value}")
        
        elif literal_type == "string":
            # Strings são ponteiros para arrays de caracteres
            str_const = f"@str{len(self.buffer)}"
            str_len = len(value) + 1  # +1 para o terminador null
            
            # Define a string constante
            self.emit(f"{str_const} = private constant [{str_len} x i8] c\"{value}\\00\"")
            
            # Obtém um ponteiro para a string
            self.emit(f"{result_temp} = getelementptr [{str_len} x i8], [{str_len} x i8]* {str_const}, i32 0, i32 0")
        
        elif literal_type == "date":
            # Datas são representadas como timestamps Unix (i32)
            # Para simplificar, não convertemos a data para timestamp
            self.emit(f"{result_temp} = call i32 @date_to_timestamp(i8* {value})")
        
        elif literal_type == "measurement":
            # Medições são tratadas como float para simplificar
            # Na realidade, precisaríamos extrair o valor numérico e a unidade
            measurement_value = "".join(c for c in value if c.isdigit() or c == '.')
            measurement_value = float(measurement_value) if measurement_value else 0.0
            
            self.emit(f"{result_temp} = {measurement_value}")
        
        else:
            # Tipo desconhecido
            self.emit(f"{result_temp} = 0")
        
        return result_temp
    
    def visit_ArrayLiteral(self, node):
        """Gera código para literais de array."""
        # Aloca memória para o array
        array_size = len(node.elements)
        
        # Cria um array de ponteiros
        array_temp = self.fresh_temp()
        self.emit(f"{array_temp} = call i8** @create_array(i32 {array_size})")
        
        # Preenche o array com os elementos
        for i, element in enumerate(node.elements):
            element_temp = self.visit(element)
            
            # Armazena o elemento no array
            self.emit(f"call void @array_set(i8** {array_temp}, i32 {i}, i8* {element_temp})")
        
        return array_temp
    
    def visit_ObjectLiteral(self, node):
        """Gera código para literais de objeto."""
        # Aloca memória para o objeto
        # Para simplificar, assumimos que é um paciente
        obj_temp = self.fresh_temp()
        self.emit(f"{obj_temp} = call %Patient* @create_patient()")
        
        # Inicializa os campos do objeto com as propriedades fornecidas
        for prop in node.properties:
            prop_name = prop.name
            prop_value_temp = self.visit(prop.value)
            
            # Obtém o campo correto com base no nome da propriedade
            field_index = {
                "id": 0,
                "name": 1,
                "birth": 2,
                "weight": 3,
                "height": 4,
                "allergies": 5
            }.get(prop_name, -1)
            
            if field_index >= 0:
                # Acessa o campo
                field_ptr_temp = self.fresh_temp()
                self.emit(f"{field_ptr_temp} = getelementptr %Patient, %Patient* {obj_temp}, i32 0, i32 {field_index}")
