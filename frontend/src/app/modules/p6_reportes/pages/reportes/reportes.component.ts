import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { ReportService } from '../../report.service';

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [CommonModule, DatePipe],
  templateUrl: './reportes.component.html',
  styleUrl: './reportes.component.css'
})
export class ReportesComponent implements OnInit {
  historial: any[] = [];
  loading = false;

  constructor(private reportService: ReportService) {}

  ngOnInit(): void {
    this.cargarHistorial();
  }

  cargarHistorial() {
    this.reportService.getHistory().subscribe({
      next: (data) => this.historial = data,
      error: (err) => console.error('Error al cargar historial', err)
    });
  }

  descargarPDF() {
    this.loading = true;
    this.reportService.getIncidentsPdf().subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Reporte_Incidentes_${new Date().getTime()}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.loading = false;
        this.cargarHistorial();
      },
      error: (err) => {
        console.error('Error al descargar PDF', err);
        this.loading = false;
      }
    });
  }

  descargarExcel() {
    this.loading = true;
    this.reportService.getIncidentsExcel().subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Reporte_Incidentes_${new Date().getTime()}.xlsx`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.loading = false;
        this.cargarHistorial();
      },
      error: (err) => {
        console.error('Error al descargar Excel', err);
        this.loading = false;
      }
    });
  }
}
