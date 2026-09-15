# Ever Gauzy Business Management Platform 🚀

[![Platform](https://img.shields.io/badge/Platform-Ever%20Gauzy%20v0.84%2B-blue)](#)
[![Stack](https://img.shields.io/badge/Stack-Node.js%20%7C%20NestJS%20%7C%20Angular%20%7C%20PostgreSQL-brightgreen)](#)
[![Deployment](https://img.shields.io/badge/Deployment-Docker%20Compose%20%7C%20Kubernetes-purple)](#)
[![Security](https://img.shields.io/badge/Security-JWT%20%7C%20RBAC%20%7C%20SSL-orange)](#)

Guia enterprise de arquitetura, configuração, integração, segurança e implantação do **Ever Gauzy** (https://github.com/ever-co/ever-gauzy) — a plataforma Open-Source de Gestão Empresarial, acompanhamento de horas, automação financeira, gestão de RH, CRM e gestão de projetos.

---

## 📋 Sumário
- [1. Visão Geral & Arquitetura](#1-visão-geral--arquitetura)
- [2. Configuração do Ambiente & Pré-requisitos](#2-configuração-do-ambiente--pré-requisitos)
- [3. Decisões Arquiteturais & Topologias](#3-decisões-arquiteturais--topologias)
- [4. Configuração de Módulos Core](#4-configuração-de-módulos-core)
- [5. Integrações Corporativas & OAuth/SSO](#5-integrações-corporativas--oauthsso)
- [6. Segurança, SSL & Boas Práticas](#6-segurança-ssl--boas-práticas)
- [7. Implantação, CI/CD & Automação](#7-implantação-cicd--automação)
- [8. Resolução de Problemas & Troubleshooting](#8-resolução-de-problemas--troubleshooting)

---

## 🗺️ 1. Visão Geral & Arquitetura

O Ever Gauzy é construído sobre uma arquitetura moderna baseada em **NestJS (TypeScript)** no backend (API REST & WebSockets) e **Angular** ou **React** no frontend. Ele suporta persistência via **PostgreSQL / SQLite** através do TypeORM ou MikroORM, e utilitários de fila assíncrona/cache com **Redis**.

### Diagrama Arquitetural Enterprise (Monólito vs Microserviços & Edge Proxy)

```
+---------------------------------------------------------------------------------+
|                                 USUÁRIOS / CLIENTES                             |
|              (Navegador Web, App Desktop Ever Gauzy, App Mobile)                |
+----------------------------------------+----------------------------------------+
                                         |
                                         v  (HTTPS / SSL - Porta 443)
+---------------------------------------------------------------------------------+
|                            NGINX / EDGE INGRESS REVERSE PROXY                   |
|       - SSL Termination (Certbot / Let's Encrypt)                               |
|       - WAF & Proteção Anti-DDoS / Rate Limiting                                |
|       - Compressão Gzip/Brotli & Roteamento de Assets Estáticos                  |
+----------------------------------------+----------------------------------------+
                                         |
                                         v  (Reverse Proxy pass to :4200 / :3000)
+---------------------------------------------------------------------------------+
|                        EVER GAUZY BACKEND / API SERVER                          |
|   - NestJS REST Controllers & GraphQL Gateway                                   |
|   - Servidor WebSocket (Real-time activity & time tracking streaming)           |
|   - JWT Authentication & RBAC / Multi-Tenant Policy Engine                     |
|   - Invoicing, Payroll, CRM, Project Management & HR Services                   |
+------------------+---------------------+-------------------+--------------------+
                   |                     |                   |
                   | (DB Read/Write)     | (Cache & Queue)   | (External APIs)
                   v                     v                   v
+------------------+----+  +-------------+-----+  +----------+--------------------+
| POSTGRESQL 16 DATABASE|  |   REDIS 7 CLUSTER   |  |   TERCEIROS & INTEGRAÇÕES      |
|                       |  |                     |  |                            |
| - Organizações        |  | - Sessões JWT &     |  | - JIRA CLOUD / GITHUB      |
| - Empregados & Timers |  |   Revogação         |  | - UPWORK & SLACK           |
| - Faturas & Pagamentos|  | - Filas BullMQ      |  | - STRIPE & PAYPAL          |
| - Multi-tenancy RLS   |  |   (Notificações)    |  | - GOOGLE / GITHUB OAUTH    |
+-----------------------+  +---------------------+  +----------------------------+
```

---

## 🛠️ 2. Configuração do Ambiente & Pré-requisitos

### Pré-requisitos do Sistema
| Componente | Versão Mínima | Versão Recomendada | Função |
|------------|---------------|-------------------|--------|
| **Node.js** | `v18.x` | `v20.x` LTS | Runtime de execução backend e build frontend |
| **Pnpm / Yarn**| `pnpm v8+` ou `yarn v1.22+` | `pnpm v9.x` | Gerenciador de pacotes monorepo |
| **Docker** | `v24.0+` | `v27.x` | Conteinerização e microsserviços |
| **Docker Compose**| `v2.20+` | `v2.29+` (Compose V2 Spec) | Orquestração local/staging |
| **PostgreSQL**| `v15.0+` | `v16.2` | Banco de dados relacional primário |
| **Redis** | `v6.2+` | `v7.2` | Cache, pub/sub e processamento de tarefas em segundo plano |

### Instalação e Execução Local
Para clonar e executar o Ever Gauzy em ambiente de desenvolvimento local:

```bash
# 1. Clonar o repositório oficial
git clone https://github.com/ever-co/ever-gauzy.git
cd ever-gauzy

# 2. Instalar dependências via pnpm
pnpm install

# 3. Configurar variáveis de ambiente
cp .env.example .env

# 4. Iniciar infraestrutura de apoio (PostgreSQL + Redis) via Docker Compose
docker-compose up -d DB Redis

# 5. Executar migrações e popular banco de dados com seeds iniciais
pnpm seed:run

# 6. Iniciar a plataforma em modo desenvolvimento (API + Frontend)
pnpm start
```

Ao finalizar a inicialização, a interface Web estará acessível em `http://localhost:4200` e a API OpenAPI/Swagger em `http://localhost:3000/api`.

---

## 📐 3. Decisões Arquiteturais & Topologias

### Monólito Integrado vs Microsserviços
1. **Implantação Monolítica (Recomendada para times de até 500 colaboradores)**:
   - A API NestJS e o Frontend Angular são servidos a partir do mesmo contêiner ou sob o mesmo proxy Nginx.
   - Baixa complexidade operacional, custo reduzido de infraestrutura e gerenciamento simplificado de transações no banco de dados.
2. **Implantação em Microsserviços / Desacoplada (Empresas de Grande Porte)**:
   - Servidor de API REST/GraphQL isolado (`ever-gauzy-api`).
   - Servidor Web desacoplado servindo apenas assets estáticos do SPA Angular via CDN/S3/Nginx.
   - Workers dedicados para tarefas em segundo plano (geração de relatórios PDF, envio de e-mails em lote, processamento de folha de pagamento).

### Escolha de Banco de Dados & Cache
- **PostgreSQL 16**: Escolhido devido à capacidade nativa de JSONB, suporte robusto a transações ACID complexas (essenciais para cálculo de folha e faturamento) e compatibilidade total com TypeORM.
- **Redis 7**: Utilizado como repositório de sessões revogadas, pub/sub de timers em tempo real e broker para tarefas diferidas (BullMQ).

---

## ⚙️ 4. Configuração de Módulos Core

### Multi-Tenancy & Organizações
O Ever Gauzy gerencia nativamente suporte a múltiplos tenants (Organizações/Empresas) no mesmo banco de dados:
- Cada entidade (`User`, `Employee`, `Invoice`, `TimeLog`) possui chave estrangeira vinculada a `tenantId` e `organizationId`.
- O isolamento é garantido na camada de serviço da API e pode ser estendido via Row-Level Security (RLS) no PostgreSQL.

### Controle de Acesso Baseado em Funções (RBAC)
Os papéis padrão pré-configurados incluem:
- `SUPER_ADMIN`: Gestão global da plataforma e criação de tenants.
- `ADMIN`: Administrador da Organização (acesso a relatórios de folha, faturamento e configurações).
- `MANAGER`: Gerente de Projetos (gestão de tarefas, aprovação de quadros de horários/timesheets).
- `EMPLOYEE`: Colaborador (registro de horas, visualização de suas tarefas e holerites).
- `CANDIDATE` / `CLIENT`: Acesso restrito para candidatos em processo seletivo e clientes para acompanhamento de faturas.

### Módulos Integrados

```text
+---------------------------------------------------------------------------------+
|                           MÓDULOS DE NEGÓCIO EVER GAUZY                         |
+------------------+---------------------+-------------------+--------------------+
|  TIME TRACKING   |  INVOICING & CRM    |  PAYROLL & HR     |  PROJECT & TASKS   |
|                  |                     |                   |                    |
| - Timers online  | - Emissão de Faturas| - Cálculo de horas| - Quadros Kanban   |
| - Captura de telas| - Cobrança Stripes | - Bônus e descontos| - Integração Jira  |
| - Atividade mouse| - Gestão de Clientes| - Férias e licenças| - Sprints e Marcos |
+------------------+---------------------+-------------------+--------------------+
```

---

## 🔌 5. Integrações Corporativas & OAuth/SSO

### Autenticação OAuth 2.0 / SSO
O Ever Gauzy permite login único via Google e GitHub configurando as seguintes chaves no `.env`:

```env
# Google OAuth
GOOGLE_CLIENT_ID=seu-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu-google-client-secret

# GitHub OAuth
GITHUB_CLIENT_ID=seu-github-client-id
GITHUB_CLIENT_SECRET=seu-github-client-secret
```

### Integrações de Terceiros

| Serviço | Utilização no Ever Gauzy | Chaves Necessárias |
|---------|--------------------------|---------------------|
| **Jira Cloud** | Sincronização bidirecional de Issues e tempo estimado/gasto | `JIRA_HOST`, `JIRA_API_KEY`, `JIRA_EMAIL` |
| **GitHub** | Vinculação de commits e PRs a tarefas do Gauzy | `GITHUB_PERSONAL_TOKEN` |
| **Upwork** | Importação de contratos e diários de trabalho | `UPWORK_CONSUMER_KEY`, `UPWORK_CONSUMER_SECRET` |
| **Slack** | Notificações de início/fim de expediente e novas faturas | `SLACK_BOT_TOKEN`, `SLACK_WEBHOOK_URL` |
| **Stripe** | Processamento automático de pagamentos de faturas | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` |
| **PayPal** | Meio alternativo de recebimento de clientes | `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` |

---

## 🛡️ 6. Segurança, SSL & Boas Práticas

1. **Autenticação JWT Segura**:
   - Os tokens JWT possuem tempo de expiração curto (ex: 15 minutos) e utilizam `REFRESH_TOKEN` armazenado em HTTP-Only Cookies seguros.
   - Segredo JWT deve ser gerado aleatoriamente com pelo menos 64 caracteres.
2. **HTTPS / SSL Termination**:
   - A terminação TLS é realizada no proxy de borda Nginx usando certificados SSL Let's Encrypt gerados via Certbot.
3. **API Rate Limiting & Securing Headers**:
   - O proxy Nginx impõe limite de requisições por IP (`zone=gauzy_limit:10m rate=10r/s`) prevenindo ataques de força bruta nas rotas `/api/auth/login`.
   - Utilização de cabeçalhos HSTS, X-Frame-Options, X-Content-Type-Options e Content-Security-Policy (CSP).

---

## 🚀 7. Implantação, CI/CD & Automação

### Execução via Docker Compose (Produção)
Um arquivo `docker-compose.yml` completo é disponibilizado nesta pasta para orquestrar o servidor Gauzy, banco de dados PostgreSQL 16, cache Redis 7 e o proxy reverso Nginx.

```bash
# Iniciar a pilha completa em segundo plano
docker compose up -d

# Verificar status dos serviços
docker compose ps
```

### Manifestos Kubernetes
Na pasta `k8s/` encontram-se os manifestos declarativos para implantação em clusters Kubernetes corporativos (AWS EKS, GCP GKE, On-Premise MicroK8s):
- `deployment.yaml`: Deployment da API/Server com 2 réplicas e probing de saúde.
- `service.yaml`: Service ClusterIP interno.
- `ingress.yaml`: Ingress Controller com suporte ao cert-manager e SSL automático.
- `configmap.yaml` & `secret.yaml`: Gerenciamento de parâmetros e segredos.

### Backup & Disaster Recovery
O script de automação em `scripts/backup_gauzy_db.sh` realiza backups diários codificados do PostgreSQL com retenção configurável de 30 dias:

```bash
# Conceder permissão e executar backup manual
chmod +x scripts/backup_gauzy_db.sh
./scripts/backup_gauzy_db.sh
```

---

## 🔍 8. Resolução de Problemas & Troubleshooting

### 1. Falha na Migração do Banco de Dados (`TypeORM Migration Error`)
* **Causa**: Incompatibilidade entre tabelas existentes e novos modelos do Ever Gauzy.
* **Solução**:
  ```bash
  # Rodar migrações manualmente
  pnpm typeorm migration:run
  ```

### 2. Conexão Recusada no Redis (`ECONNREFUSED 127.0.0.1:6379`)
* **Causa**: Redis não está em execução ou o nome da variável `REDIS_HOST` no `.env` aponta para `localhost` dentro do contêiner Docker.
* **Solução**: Altere `REDIS_HOST=redis` no arquivo `.env` para apontar para o nome do serviço no Docker Compose.

### 3. Erro de Permissão no Upload de Imagens / Logos / Capturas de Tela
* **Causa**: O contêiner da aplicação não tem permissão de escrita no diretório persistente de uploads.
* **Solução**: Garantir que o volume `./uploads` possui permissões adequadas:
  ```bash
  chmod -R 777 ./uploads
  ```
