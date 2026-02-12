# 🌐 Configuración de RDS para Acceso Cross-Region

## Problema
Lambda está en **us-west-1** pero RDS está en **us-east-1**. Para que se puedan comunicar, necesitas hacer RDS públicamente accesible.

---

## ⚙️ Pasos para Configurar RDS

### 1. Ir a la Consola de RDS

Ve a: https://console.aws.amazon.com/rds/home?region=us-east-1#databases:

### 2. Seleccionar tu instancia RDS

- Click en: `quinta-dev-instance-1`

### 3. Hacer la instancia públicamente accesible

1. Click en **Modify** (botón naranja arriba a la derecha)
2. Busca la sección **Connectivity**
3. Encuentra **Public access**
4. Selecciona: **Yes** ✅
5. Scroll hasta el final
6. Click **Continue**
7. Selecciona: **Apply immediately** ✅
8. Click **Modify DB instance**

⏳ Espera ~2-5 minutos mientras se aplican los cambios.

---

### 4. Configurar Security Group

El Security Group debe permitir conexiones MySQL (puerto 3306) desde internet.

**Pasos:**

1. En la consola de RDS, click en tu instancia `quinta-dev-instance-1`
2. En la tab **Connectivity & security**
3. Busca **VPC security groups** → Click en el security group (empieza con `sg-...`)
4. Click en la tab **Inbound rules**
5. Click **Edit inbound rules**
6. Click **Add rule**
7. Configura:
   - **Type**: MySQL/Aurora (puerto 3306 se selecciona automáticamente)
   - **Source**: `0.0.0.0/0` (permite desde cualquier IP)
   - **Description**: `Allow Lambda cross-region access`
8. Click **Save rules**

---

### 5. Obtener el Endpoint Público

1. Vuelve a la consola de RDS
2. Click en tu instancia `quinta-dev-instance-1`
3. En **Endpoint & port**, verás algo como:
   ```
   quinta-dev-instance-1.cl6gc8eym99u.us-east-1.rds.amazonaws.com:3306
   ```
4. ✅ Este endpoint ya debería ser el mismo que tienes en tu `.env`

---

## ⚠️ Consideraciones de Seguridad

**Riesgos de hacer RDS público:**
- ⚠️ La base de datos es accesible desde internet
- ⚠️ Cualquiera puede intentar conectarse (aunque necesita usuario/password)

**Recomendaciones:**
1. ✅ Usa una contraseña fuerte (ya la tienes)
2. ✅ Considera usar un Security Group que solo permita IPs específicas si es posible
3. ✅ Habilita SSL/TLS para conexiones encriptadas
4. ✅ En producción, considera usar VPC Peering entre regiones (más seguro)

---

## 🧪 Verificar la Configuración

Una vez que RDS esté público:

### Test local:
```bash
node test-lambda.js
```

Debería mostrar:
```
✅ Connected successfully!
✅ Query test: [ { test: 1 } ]
✅ Connection closed
```

### Test en Lambda:
Una vez deployado, prueba:
```
https://uved82gwyg.execute-api.us-west-1.amazonaws.com/dev/api/tires
```

---

## 📝 Checklist

- [ ] RDS configurado como públicamente accesible
- [ ] Security Group permite puerto 3306 desde 0.0.0.0/0
- [ ] Test local funciona con `node test-lambda.js`
- [ ] Push de código con región us-west-1
- [ ] Deploy en GitHub Actions completado
- [ ] API funciona correctamente

---

## 🚨 Si sigue sin funcionar

Si después de configurar RDS público sigues viendo error 502:

1. Verifica que el endpoint en `MYSQL_URI` sea el correcto
2. Verifica que el security group permita puerto 3306
3. Revisa los logs de CloudWatch para ver el error exacto

¿Necesitas ayuda con alguno de estos pasos?
