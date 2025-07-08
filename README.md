# 🚀 AI Invoice Agent

> **Microserviço simplificado para extração automática de transações de faturas de cartão de crédito**

Este projeto fornece uma API REST que processa PDFs de faturas e extrai dados estruturados de transações usando inteligência artificial.

## 📋 Funcionalidades

- **📄 Processamento de PDFs**: Extração otimizada de texto com fallback OCR
- **🏦 Detecção de Instituições**: Suporte para Caixa, Nubank, Banco do Brasil, Bradesco, Itaú
- **🤖 Múltiplos Providers de IA**: OpenAI (GPT-4o-mini) e DeepSeek
- **✅ Validação Completa**: 7 regras de validação para garantir qualidade dos dados
- **🔄 Retry Logic**: Tratamento robusto de falhas temporárias
- **📊 Monitoramento**: Health checks para orquestração de containers

## 🏗️ Arquitetura Simplificada

```
ai-invoice-agent/
├── app/
│   ├── main.py              # FastAPI + todas as rotas
│   ├── extractor.py         # Lógica principal de extração
│   ├── models.py           # Modelos Pydantic
│   ├── utils.py            # PDF processing + validação
│   └── providers/          # Providers de IA
│       ├── __init__.py     # Factory pattern
│       ├── base.py         # Interface abstrata
│       ├── prompts.py      # Prompts por instituição
│       ├── openai.py       # Implementação OpenAI
│       └── deepseek.py     # Implementação DeepSeek
└── tests/                  # Testes automatizados
```

**Padrão Arquitetural**: Service API com Strategy Pattern para providers

## ⚡ Quick Start

### 1. **Instalação**

```bash
# Clone o repositório
git clone https://github.com/your-org/ai-invoice-agent.git
cd ai-invoice-agent

# Instalar dependências (Poetry)
poetry install

# Ou via pip
pip install -r requirements.txt
```

### 2. **Configuração**

```bash
# Copiar arquivo de ambiente
cp env.example .env

# Editar variáveis (obrigatório: API keys)
nano .env
```

**Variáveis essenciais**:

```env
# API Keys (pelo menos uma é obrigatória)
OPENAI_API_KEY=sk-your-openai-key
DEEPSEEK_API_KEY=your-deepseek-key

# Configurações opcionais
DEFAULT_AI_PROVIDER=openai        # ou deepseek
ENVIRONMENT=development           # ou production
DEBUG=true                       # ou false
MAX_FILE_SIZE=10485760           # 10MB
```

### 3. **Executar**

```bash
# Desenvolvimento
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ou com Python
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Produção
python app/main.py
```

### 4. **Docker (Recomendado)**

```bash
# Build da imagem
docker build -t ai-invoice-agent .

# Executar container
docker run -d \
  --name invoice-agent \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e DEFAULT_AI_PROVIDER=openai \
  ai-invoice-agent

# Ou usar docker-compose
docker-compose up -d
```

## 📚 Uso da API

### **Endpoints Principais**

| Endpoint              | Método | Descrição                  |
| --------------------- | ------ | -------------------------- |
| `/`                   | GET    | Informações básicas da API |
| `/health`             | GET    | Health check detalhado     |
| `/health/ready`       | GET    | Readiness check para K8s   |
| `/v1/`                | GET    | Informações da API v1      |
| `/v1/process-invoice` | POST   | **Processar fatura PDF**   |

### **Exemplo de Uso**

```bash
# Upload de PDF com OpenAI
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@fatura.pdf" \
  -F "provider=openai"

# Upload de PDF com DeepSeek
curl -X POST http://localhost:8000/v1/process-invoice \
  -F "file=@fatura.pdf" \
  -F "provider=deepseek"
```

### **Resposta Estruturada**

```json
{
  "transactions": [
    {
      "date": "2025-01-15",
      "description": "UBER TRIP 001",
      "amount": 25.5,
      "type": "debit",
      "installments": 1,
      "current_installment": 1,
      "total_purchase_amount": 25.5,
      "due_date": "2025-02-20",
      "category": "transport"
    }
  ],
  "metadata": {
    "processing_time_ms": 1250,
    "total_transactions": 15,
    "confidence_score": 0.95,
    "provider": "openai",
    "institution": "CAIXA"
  },
  "errors": null
}
```

## 🔧 Configuração Avançada

### **Providers de IA**

#### **OpenAI (Recomendado)**

- **Modelo**: GPT-4o-mini
- **Custo**: ~$0.15/1M tokens de entrada
- **Qualidade**: Excelente para textos estruturados
- **Configuração**: Apenas `OPENAI_API_KEY`

#### **DeepSeek (Alternativa)**

- **Modelo**: deepseek-chat
- **Custo**: ~$0.27/1M tokens de entrada
- **Qualidade**: Boa para textos complexos
- **Configuração**: Apenas `DEEPSEEK_API_KEY`

### **Validações Aplicadas**

1. **Campos obrigatórios**: data, descrição, valor
2. **Sem duplicatas**: transações idênticas são rejeitadas
3. **Datas válidas**: não podem ser futuras ou após vencimento
4. **Faixa de valores**: R$ 0,01 a R$ 100.000
5. **Consistência de parcelas**: total = valor × parcelas
6. **Data de vencimento**: consistente entre todas as transações
7. **Soma válida**: total das transações = total da fatura (±R$ 0,01)

## 🛠️ Desenvolvimento

### **Estrutura de Testes**

```bash
# Executar todos os testes
poetry run pytest

# Executar com coverage
poetry run pytest --cov=app

# Testes específicos
poetry run pytest tests/test_models.py
```

### **Extensão de Providers**

Para adicionar um novo provider de IA:

1. **Criar implementação**:

```python
# app/providers/claude.py
class ClaudeProvider(AIProvider):
    @property
    def name(self) -> str:
        return "claude"

    async def extract_transactions(self, text: str, institution: str):
        # Implementação específica
        pass
```

2. **Registrar no factory**:

```python
# app/providers/__init__.py
PROVIDERS = {
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
    "claude": ClaudeProvider,  # Novo provider
}
```

3. **Adicionar prompts**:

```python
# app/providers/prompts.py
PROVIDER_ADJUSTMENTS = {
    "claude": {
        "extra_instructions": "...",
        "temperature": 0,
        "max_tokens": 1500
    }
}
```

## 🚀 Deploy

### **Google Cloud Run**

```bash
# Build e deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/ai-invoice-agent
gcloud run deploy --image gcr.io/PROJECT-ID/ai-invoice-agent --platform managed
```

### **Kubernetes**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-invoice-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-invoice-agent
  template:
    metadata:
      labels:
        app: ai-invoice-agent
    spec:
      containers:
        - name: ai-invoice-agent
          image: ai-invoice-agent:latest
          ports:
            - containerPort: 8000
          env:
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: ai-secrets
                  key: openai-key
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
```

## 📊 Monitoramento

### **Health Checks**

- **Liveness**: `/health` - Verifica se a aplicação está funcionando
- **Readiness**: `/health/ready` - Verifica se está pronta para receber tráfego

### **Métricas Incluídas**

- Tempo de processamento (ms)
- Score de confiança da IA
- Número de transações extraídas
- Provider utilizado
- Instituição detectada

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma feature branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

**Desenvolvido com ❤️ para automatizar o processamento de faturas brasileiras**
