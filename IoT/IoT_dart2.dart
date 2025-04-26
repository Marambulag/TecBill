import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: DistributorScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class DistributorScreen extends StatelessWidget {
  // Función para mostrar el cuadro de diálogo de correo electrónico
  Future<void> solicitarAnalisis(BuildContext context) async {
    TextEditingController emailController = TextEditingController();

    // Mostrar cuadro de diálogo para ingresar el correo electrónico
    await showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Recibir Análisis'),
          content: TextField(
            controller: emailController,
            decoration: InputDecoration(
              labelText: 'Correo Electrónico',
              hintText: 'ejemplo@correo.com',
            ),
            keyboardType: TextInputType.emailAddress,
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Cancelar'),
            ),
            TextButton(
              onPressed: () async {
                Navigator.pop(context);
                String email = emailController.text.trim();
                if (email.isNotEmpty) {
                  await enviarCorreoAnalisis(context, email);
                } else {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text("El correo no puede estar vacío.")),
                  );
                }
              },
              child: Text('Enviar'),
            ),
          ],
        );
      },
    );
  }

  // Función para enviar el análisis por correo electrónico
  Future<void> enviarCorreoAnalisis(BuildContext context, String email) async {
    final url = Uri.parse('http://localhost:5000/enviar_correo');

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'destinatario': email,
          'asunto': 'Análisis de Ventas',
          'mensaje': 'Adjunto encontrarás el análisis solicitado de las ventas.',
          'archivo_adjunto': 'grafico.png', // Nombre del archivo generado en Flask
        }),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('El análisis fue enviado exitosamente.')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text('Error al enviar el análisis: ${response.body}')),
        );
      }
    } catch (error) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error al conectar con el servidor: $error")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Distribuidor o Administrador'),
        backgroundColor: Colors.blue,
      ),
      body: Center(