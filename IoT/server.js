const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const app = express();
const port = 3001;

app.use(cors());
app.use(express.json());

// Configuración de la conexión a la base de datos
const connection = mysql.createConnection({
    host: "10.43.127.176",
    user: "root",
    password: "1234",
    database: "autobill"
});

// Conectar a la base de datos
connection.connect((err) => {
    if (err) {
        console.error('Error al conectar a la base de datos:', err);
        return;
    }
    console.log('Conectado a la base de datos MariaDB');
});

// Ruta para obtener los productos en el carrito
app.get('/carrito', (req, res) => {
    const query = `
        SELECT p.nombre, 
               COALESCE(p.cantidad, 0) AS stock, 
               COALESCE(CAST(p.precio AS FLOAT), 0.0) AS precio, 
               COALESCE(cp.cantidad, 0) AS cantidad_en_carrito
        FROM carrito_producto cp
        JOIN producto p ON cp.id_producto = p.ID
        WHERE cp.id_carrito = (
            SELECT MAX(id_carrito) 
            FROM carrito 
            WHERE estado = 'activo'
        )`;

    connection.query(query, (err, productos) => {
        if (err) {
            console.error('Error al consultar los productos del carrito:', err);
            return res.status(500).send('Error al consultar la base de datos');
        }

        if (productos.length === 0) {
            return res.status(404).json({ message: 'No se encontraron productos en el carrito activo' });
        }

        console.log('Productos obtenidos:', productos);
        res.json(productos); // Devuelve los productos como respuesta JSON
    });
});

// Ruta para actualizar el carrito
app.post('/actualizar-carrito', (req, res) => {
    const { idCarrito, idProducto, cantidad } = req.body;

    if (!idCarrito || !idProducto || cantidad === undefined) {
        return res.status(400).json({ error: 'idCarrito, idProducto y cantidad son requeridos' });
    }

    const query = `
        UPDATE carrito_producto
        SET cantidad = ?
        WHERE id_carrito = ? AND id_producto = ?`;

    connection.query(query, [cantidad, idCarrito, idProducto], (err, result) => {
        if (err) {
            console.error('Error al actualizar el carrito:', err);
            return res.status(500).send('Error al actualizar la base de datos');
        }

        console.log('Carrito actualizado:', result);
        res.json({ message: 'Carrito actualizado con éxito' });
    });
});

// Ruta para finalizar la compra
app.post('/finalizar-compra', (req, res) => {
    const { idCarrito } = req.body;

    if (!idCarrito) {
        return res.status(400).json({ error: 'idCarrito es requerido' });
    }

    const query = `
        UPDATE carrito
        SET estado = 'finalizado'
        WHERE id_carrito = ?`;

    connection.query(query, [idCarrito], (err, result) => {
        if (err) {
            console.error('Error al finalizar la compra:', err);
            return res.status(500).send('Error al finalizar la compra');
        }

        console.log('Compra finalizada:', result);
        res.json({ message: 'Compra finalizada con éxito' });
    });
});

// Ruta para refrescar el carrito (obtener productos actuales)
app.post('/refresh-carrito', (req, res) => {
    const query = `
        SELECT p.nombre, 
               COALESCE(p.cantidad, 0) AS stock, 
               COALESCE(CAST(p.precio AS FLOAT), 0.0) AS precio, 
               COALESCE(cp.cantidad, 0) AS cantidad_en_carrito
        FROM carrito_producto cp
        JOIN producto p ON cp.id_producto = p.ID
        WHERE cp.id_carrito = (
            SELECT MAX(id_carrito)
            FROM carrito
            WHERE estado = 'activo'
        )`;

    connection.query(query, (err, productos) => {
        if (err) {
            console.error('Error al refrescar los productos del carrito:', err);
            return res.status(500).send('Error al refrescar el carrito');
        }

        if (productos.length === 0) {
            return res.status(404).json({ message: 'No se encontraron productos en el carrito activo' });
        }

        console.log('Carrito refrescado:', productos);
        res.json({ message: 'Carrito refrescado con éxito', carrito: productos });
    });
});

// Iniciar el servidor
app.listen(port, () => {
    console.log(`Servidor escuchando en http://localhost:${port}`);
});
