import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AnalyticsService, DashboardKPIs } from '../../services/analytics.service';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  analyticsService = inject(AnalyticsService);
  kpis: DashboardKPIs | null = null;
  loading = true;

  // Pie
  public pieChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    plugins: {
      legend: { display: true, position: 'top' },
    }
  };
  public pieChartData: ChartData<'pie', number[], string | string[]> = {
    labels: [],
    datasets: [{ data: [] }]
  };
  public pieChartType: ChartType = 'pie';

  // Bar
  public barChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    scales: { x: {}, y: { min: 0 } },
    plugins: {
      legend: { display: true },
    }
  };
  public barChartType: ChartType = 'bar';
  public barChartData: ChartData<'bar'> = {
    labels: [],
    datasets: []
  };

  ngOnInit(): void {
    this.analyticsService.getDashboardKPIs().subscribe({
      next: (data) => {
        this.kpis = data;
        
        // Categoria (Pie)
        this.pieChartData.labels = Object.keys(data.incidentes_por_categoria);
        this.pieChartData.datasets[0].data = Object.values(data.incidentes_por_categoria);

        // Talleres Eficientes (Bar)
        this.barChartData.labels = data.talleres_mas_eficientes.map(t => t.nombre);
        this.barChartData.datasets = [
          { data: data.talleres_mas_eficientes.map(t => t.avg_resolucion_min), label: 'Minutos Promedio', backgroundColor: '#3b82f6' }
        ];

        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading KPIs', err);
        this.loading = false;
      }
    });
  }
}
