import { Routes } from '@angular/router';
import { authGuard } from './modules/shared/guards/auth.guard';
import { roleGuard } from './modules/shared/guards/role.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./modules/shared/pages/landing-page.component').then((m) => m.LandingPageComponent),
  },

  // ── P1: Autenticación (públicas) ──
  {
    path: 'login',
    loadComponent: () => import('./modules/p1_usuarios/pages/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    loadComponent: () => import('./modules/p1_usuarios/pages/register/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'forgot-password',
    loadComponent: () => import('./modules/p1_usuarios/pages/forgot-password/forgot-password.component').then((m) => m.ForgotPasswordComponent),
  },
  {
    path: 'reset-password',
    loadComponent: () => import('./modules/p1_usuarios/pages/reset-password/reset-password.component').then((m) => m.ResetPasswordComponent),
  },

  // ── P1: Protegidas ──
  {
    path: 'home',
    loadComponent: () => import('./modules/p1_usuarios/pages/home/home.component').then((m) => m.HomeComponent),
    canActivate: [authGuard],
  },
  {
    path: 'admin-users',
    loadComponent: () => import('./modules/p1_usuarios/pages/admin-users/admin-users.component').then((m) => m.AdminUsersComponent),
    canActivate: [authGuard, roleGuard('admin')],
  },

  // ── P2: Incidentes ──
  {
    path: 'incidents',
    loadComponent: () => import('./modules/p2_incidentes/pages/incidents/my-incidents/my-incidents.component').then((m) => m.MyIncidentsComponent),
    canActivate: [authGuard],
  },
  {
    path: 'incidents/report',
    loadComponent: () => import('./modules/p2_incidentes/pages/incidents/report-incident/report-incident.component').then((m) => m.ReportIncidentComponent),
    canActivate: [authGuard],
  },
  {
    path: 'incidents/:id',
    loadComponent: () => import('./modules/p2_incidentes/pages/incidents/incident-detail/incident-detail.component').then((m) => m.IncidentDetailComponent),
    canActivate: [authGuard],
  },

  // ── P3: Talleres ──
  {
    path: 'workshops/register',
    loadComponent: () =>
      import('./modules/p3_talleres/pages/workshops/register-workshop/register-workshop.component').then((m) => m.RegisterWorkshopComponent),
    canActivate: [authGuard, roleGuard('taller', 'admin')],
  },
  {
    path: 'workshops/requests',
    loadComponent: () =>
      import('./modules/p3_talleres/pages/workshops/service-requests/service-requests.component').then((m) => m.ServiceRequestsComponent),
    canActivate: [authGuard, roleGuard('taller', 'admin')],
  },
  {
    path: 'workshops/history',
    loadComponent: () =>
      import('./modules/p3_talleres/pages/workshops/service-history/service-history.component').then((m) => m.ServiceHistoryComponent),
    canActivate: [authGuard, roleGuard('taller', 'admin')],
  },

  // ── P5: Pagos y Notificaciones (CU16-CU18) ──
  {
    path: 'payments',
    loadComponent: () => import('./modules/p5_pagos/pages/payments/payments.component').then(m => m.PaymentsComponent),
    canActivate: [authGuard]
  },

  // ── P4/CU15: Seguimiento GPS ──
  {
    path: 'tracking/:id',
    loadComponent: () => import('./modules/p4_asignacion/pages/geo-tracking/geo-tracking.component').then(m => m.GeoTrackingComponent),
    canActivate: [authGuard]
  },

  // ── P8: Conectividad Resiliente y Tiempo Real (Ciclo 4) ──
  {
    path: 'realtime/tracking/:id',
    loadComponent: () => import('./modules/p8_realtime/pages/incident-tracking/incident-tracking.component').then(m => m.IncidentTrackingComponent),
    canActivate: [authGuard]
  },
  {
    path: 'realtime/timeline/:id',
    loadComponent: () => import('./modules/p8_realtime/pages/incident-timeline/incident-timeline.component').then(m => m.IncidentTimelineComponent),
    canActivate: [authGuard]
  },

  // ── P6: Reportes (CU19-CU20) ──
  {
    path: 'reports',
    loadComponent: () => import('./modules/p6_reportes/pages/reportes/reportes.component').then(m => m.ReportesComponent),
    canActivate: [authGuard, roleGuard('admin')]
  },

  // ── Catch-all ──
  { path: '**', redirectTo: 'home' },
];
