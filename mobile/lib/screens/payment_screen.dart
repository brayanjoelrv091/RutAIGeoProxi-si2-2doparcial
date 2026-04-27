import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:rutaigeoproxi_mobile/config.dart';

class PaymentScreen extends StatefulWidget {
  final int incidentId;
  final double amount;

  const PaymentScreen({
    super.key,
    required this.incidentId,
    required this.amount,
  });

  @override
  State<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  bool _isProcessing = false;
  bool _isSuccess = false;
  int _selectedMethod = 0; // 0 = Tarjeta, 1 = QR Simple

  Future<void> _processPayment() async {
    setState(() => _isProcessing = true);

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.baseUrl}/payments/process'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'incidente_id': widget.incidentId,
          'monto': widget.amount,
          'metodo_pago': _selectedMethod == 0 ? 'tarjeta_mobile' : 'qr_mobile',
        }),
      );

      if (response.statusCode == 201) {
        setState(() {
          _isProcessing = false;
          _isSuccess = true;
        });
      } else {
        throw Exception('Error en el servidor');
      }
    } catch (e) {
      setState(() => _isProcessing = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al procesar pago: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      appBar: AppBar(
        title: const Text('Pasarela de Pago'),
        backgroundColor: const Color(0xFF111629),
        elevation: 0,
      ),
      body: _isSuccess ? _buildSuccess() : _buildPaymentMethods(),
    );
  }

  Widget _buildPaymentMethods() {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF111629),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF00F2FF).withOpacity(0.3)),
          ),
          child: Column(
            children: [
              const Text('TOTAL A PAGAR', style: TextStyle(color: Colors.white54, fontSize: 14)),
              const SizedBox(height: 8),
              Text(
                'Bs. ${widget.amount.toStringAsFixed(2)}',
                style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              const Text('Incluye comisión e impuestos', style: TextStyle(color: Colors.white38, fontSize: 12)),
            ],
          ),
        ),
        const SizedBox(height: 30),
        
        Row(
          children: [
            Expanded(
              child: _MethodTab(
                icon: Icons.credit_card,
                label: 'Tarjeta',
                isSelected: _selectedMethod == 0,
                onTap: () => setState(() => _selectedMethod = 0),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _MethodTab(
                icon: Icons.qr_code_2,
                label: 'QR Simple',
                isSelected: _selectedMethod == 1,
                onTap: () => setState(() => _selectedMethod = 1),
              ),
            ),
          ],
        ),
        const SizedBox(height: 30),
        
        if (_selectedMethod == 0) _buildCardForm() else _buildQRForm(),
        
        const SizedBox(height: 40),
        ElevatedButton(
          onPressed: _isProcessing ? null : _processPayment,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF00F2FF),
            foregroundColor: Colors.black,
            minimumSize: const Size(double.infinity, 55),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            elevation: 10,
            shadowColor: const Color(0xFF00F2FF).withOpacity(0.5),
          ),
          child: _isProcessing
              ? const CircularProgressIndicator(color: Colors.black)
              : Text(
                  'CONFIRMAR PAGO DE BS. ${widget.amount.toStringAsFixed(2)}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
        ),
      ],
    );
  }

  Widget _buildCardForm() {
    return Column(
      children: [
        _buildInputField('Titular de la Tarjeta', 'EJ: JUAN PEREZ'),
        const SizedBox(height: 16),
        _buildInputField('Número de Tarjeta', '4555 0000 0000 0000', icon: Icons.credit_card),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: _buildInputField('Vencimiento', 'MM/AA')),
            const SizedBox(width: 16),
            Expanded(child: _buildInputField('CVV', '123')),
          ],
        )
      ],
    );
  }

  Widget _buildQRForm() {
    return Column(
      children: [
        const Text(
          'Escanea este QR desde tu app bancaria para proceder con el pago rápido.',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.white70),
        ),
        const SizedBox(height: 20),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
          child: const Icon(Icons.qr_code_2, size: 200, color: Colors.black),
        ),
      ],
    );
  }

  Widget _buildInputField(String label, String hint, {IconData? icon}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
        const SizedBox(height: 8),
        TextField(
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: const TextStyle(color: Colors.white24),
            prefixIcon: icon != null ? Icon(icon, color: Colors.white54) : null,
            filled: true,
            fillColor: const Color(0xFF111629),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
          ),
          style: const TextStyle(color: Colors.white),
        ),
      ],
    );
  }

  Widget _buildSuccess() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Icon(Icons.check_circle, size: 120, color: Color(0xFF00E676)),
        const SizedBox(height: 24),
        const Text('¡PAGO EXITOSO!', style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        const Text('Se ha notificado al taller y procesado la comisión de la app.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white70, fontSize: 16)),
        const SizedBox(height: 40),
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('VOLVER AL INICIO', style: TextStyle(color: Color(0xFF00F2FF), fontSize: 18)),
        ),
      ],
    );
  }
}

class _MethodTab extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _MethodTab({required this.icon, required this.label, required this.isSelected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF00F2FF).withOpacity(0.1) : Colors.transparent,
          border: Border.all(color: isSelected ? const Color(0xFF00F2FF) : Colors.white24),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Icon(icon, color: isSelected ? const Color(0xFF00F2FF) : Colors.white54, size: 32),
            const SizedBox(height: 8),
            Text(label, style: TextStyle(color: isSelected ? const Color(0xFF00F2FF) : Colors.white54, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }
}
