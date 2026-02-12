# 🚀 Guía de Configuración de Deploy Automático

## Configuración de Secrets en GitHub

Para que el deploy automático funcione, necesitas configurar los **secrets** en tu repositorio de GitHub:

### Pasos:

1. **Ve a tu repositorio** en GitHub
2. Navega a: **Settings** → **Secrets and variables** → **Actions**
3. Haz click en **New repository secret**
4. Crea los siguientes secrets:

#### Secret 1: `AWS_ACCESS_KEY_ID`
- **Name**: `AWS_ACCESS_KEY_ID`
- **Value**: Tu Access Key ID de AWS
  - Puedes obtenerla desde AWS Console → IAM → Users → Security credentials

#### Secret 2: `AWS_SECRET_ACCESS_KEY`
- **Name**: `AWS_SECRET_ACCESS_KEY`
- **Value**: Tu Secret Access Key de AWS
  - Aparece cuando creas el Access Key (guárdala de forma segura)

#### Secret 3: `MYSQL_URI`
- **Name**: `MYSQL_URI`
- **Value**: Tu URI de conexión a MySQL
  - Copia el valor desde tu archivo `.env` local:
    ```
    mysql+mysqlconnector://user:password@host:port/database
    ```

---

## Permisos IAM Necesarios

Tu usuario de AWS debe tener estos permisos:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "apigateway:*",
        "iam:GetRole",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "cloudformation:*",
        "s3:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## ✅ Cómo funciona el Deploy Automático

1. **Push a `main`**: Cada vez que haces push a la rama `main`, se ejecuta automáticamente el deploy
2. **Deploy manual**: También puedes ejecutarlo manualmente desde:
   - GitHub → **Actions** tab → **Deploy to AWS Lambda** → **Run workflow**

---

## 🧪 Probar localmente ANTES de hacer push

### 1. Instalar dependencias
```bash
npm install
```

### 2. Probar con Serverless Offline (simula API Gateway localmente)
```bash
npm run dev
```
Esto iniciará un servidor local en: `http://localhost:3000`

### 3. Deploy manual a AWS (desde tu máquina)
```bash
# Asegúrate de tener AWS CLI configurado
aws configure

# Hacer deploy
npm run deploy

# Ver información del deployment
npm run info

# Ver logs en tiempo real
npm run logs
```

---

## 📝 Scripts disponibles

| Comando | Descripción |
|---------|-------------|
| `npm start` | Ejecuta el servidor localmente (sin Serverless) |
| `npm run dev` | Ejecuta con Serverless Offline (simula API Gateway) |
| `npm run deploy` | Deploy a AWS con Serverless Framework |
| `npm run deploy:manual` | Deploy con el script antiguo (crea ZIP) |
| `npm run info` | Muestra información del deployment actual |
| `npm run logs` | Muestra logs de Lambda en tiempo real |

---

## 🎯 Endpoints después del deploy

Una vez deployado, Serverless te mostrará los endpoints:

```
endpoints:
  ANY - https://xxxxxxx.execute-api.us-west-1.amazonaws.com/dev
  ANY - https://xxxxxxx.execute-api.us-west-1.amazonaws.com/dev/{proxy+}
```

Tus rutas de API serán:
- `GET https://xxxxxxx.execute-api.us-west-1.amazonaws.com/dev/api/tires`
- `POST https://xxxxxxx.execute-api.us-west-1.amazonaws.com/dev/api/tires`
- `GET https://xxxxxxx.execute-api.us-west-1.amazonaws.com/dev/api/filters`
- etc.

---

## 🔍 Verificar el Deploy

### Opción 1: Ver en GitHub Actions
1. Ve a tu repo → **Actions**
2. Verifica que el workflow se ejecutó exitosamente (✅ verde)
3. Revisa los logs para ver el endpoint generado

### Opción 2: Probar la API
```bash
# Reemplaza {tu-endpoint} con el endpoint real
curl https://{tu-endpoint}/dev/api/tires

# Debería retornar JSON con:
# {"success": true, "data": [...], "pagination": {...}}
```

---

## ⚠️ Notas Importantes

1. **Stage**: Por defecto usa `dev`. Para cambiar a `production`:
   ```bash
   npm run deploy -- --stage production
   ```

2. **Región**: Configurada en `us-west-1` (igual que tu Lambda actual)

3. **CORS**: Ya está habilitado para todas las rutas

4. **Cold Start**: La primera petición puede tardar ~3-5 segundos (Lambda warm-up)

5. **Rollback**: Si algo falla, puedes eliminar todo con:
   ```bash
   npx serverless remove
   ```

---

## 🐛 Troubleshooting

### Error: "Cannot find module"
```bash
# Reinstalar dependencias
rm -rf node_modules
npm install
```

### Error: "AWS credentials not found"
```bash
# Configurar AWS CLI
aws configure
```

### Error: "Rate exceeded"
- Espera unos minutos, CloudFormation tiene límites de rate

### La API retorna 502 Bad Gateway
- Verifica los logs: `npm run logs`
- Asegúrate que `MYSQL_URI` esté configurado correctamente en GitHub Secrets

---

## 📦 Siguiente paso

1. **Configura los secrets** en GitHub (ver arriba)
2. **Haz un commit y push** a `main`:
   ```bash
   git add .
   git commit -m "Add automated deployment with GitHub Actions"
   git push origin main
   ```
3. **Ve a Actions tab** en GitHub para ver el deploy en vivo
4. **Prueba el endpoint** que aparecerá en los logs

¡Listo! 🎉
