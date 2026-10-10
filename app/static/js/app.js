let currentSeverityFilter = null;
let loginModalInstance = null;
let severityChartInstance = null;
let vendorChartInstance = null;
let allDevicesCache = [];

let allSyslogEventsCache = [];
let allIncidentsCache = [];

function openEventsFilterModal(filterType) {
    const modalEl = document.getElementById('customEventsFilterModal');
    const titleEl = document.getElementById('events-modal-title');
    const thead = document.getElementById('events-modal-thead');
    const tbody = document.getElementById('events-modal-tbody');

    if (filterType === 'critical') {
        if (titleEl) titleEl.innerText = "Eventos Críticos (Nivel 0 - 3)";
        if (thead) {
            thead.innerHTML = `
                <tr>
                    <th>Fecha / Hora</th>
                    <th>Origen IP</th>
                    <th>Severidad</th>
                    <th>Mensaje Log</th>
                </tr>`;
        }
        const filtered = allSyslogEventsCache.filter(e => e.severity <= 3);
        if (tbody) {
            tbody.innerHTML = filtered.map(e => `
                <tr>
                    <td><small class="text-muted">${e.timestamp ? e.timestamp.replace('T', ' ').substring(0, 19) : '-'}</small></td>
                    <td><code>${e.source_ip}</code></td>
                    <td><span class="badge badge-severity-${e.severity}">${e.severity_name} (${e.severity})</span></td>
                    <td><small class="font-monospace">${escapeHtml(e.message)}</small></td>
                </tr>
            `).join('') || `<tr><td colspan="4" class="text-center text-muted">No hay eventos críticos registrados.</td></tr>`;
        }
    } 
    else if (filterType === 'warning') {
        if (titleEl) titleEl.innerText = "Advertencias (Nivel 4)";
        if (thead) {
            thead.innerHTML = `
                <tr>
                    <th>Fecha / Hora</th>
                    <th>Origen IP</th>
                    <th>Severidad</th>
                    <th>Mensaje Log</th>
                </tr>`;
        }
        const filtered = allSyslogEventsCache.filter(e => e.severity === 4);
        if (tbody) {
            tbody.innerHTML = filtered.map(e => `
                <tr>
                    <td><small class="text-muted">${e.timestamp ? e.timestamp.replace('T', ' ').substring(0, 19) : '-'}</small></td>
                    <td><code>${e.source_ip}</code></td>
                    <td><span class="badge badge-severity-${e.severity}">${e.severity_name} (${e.severity})</span></td>
                    <td><small class="font-monospace">${escapeHtml(e.message)}</small></td>
                </tr>
            `).join('') || `<tr><td colspan="4" class="text-center text-muted">No hay advertencias registradas.</td></tr>`;
        }
    } 
    else if (filterType === 'incidents') {
        if (titleEl) titleEl.innerText = "Incidentes Activos del NOC";
        if (thead) {
            thead.innerHTML = `
                <tr>
                    <th>ID</th>
                    <th>Título</th>
                    <th>Dispositivo</th>
                    <th>Prioridad</th>
                    <th>Estado</th>
                    <th>Responsable</th>
                </tr>`;
        }
        if (tbody) {
            tbody.innerHTML = allIncidentsCache.map(i => `
                <tr>
                    <td><small class="text-muted">#${i.id}</small></td>
                    <td class="fw-bold">${escapeHtml(i.title)}</td>
                    <td><span class="badge bg-secondary">${escapeHtml(i.device_hostname || 'N/A')}</span></td>
                    <td><span class="badge bg-${i.priority === 'Critical' ? 'danger' : 'warning'}">${i.priority}</span></td>
                    <td><span class="badge bg-info">${i.status}</span></td>
                    <td><small>${escapeHtml(i.assignee)}</small></td>
                </tr>
            `).join('') || `<tr><td colspan="6" class="text-center text-muted">No hay incidentes activos registrados.</td></tr>`;
        }
    }

    if (modalEl) modalEl.classList.remove('d-none');
}

function closeEventsFilterModal() {
    const modalEl = document.getElementById('customEventsFilterModal');
    if (modalEl) modalEl.classList.add('d-none');
}

function openVendorDevicesModal(vendorName) {
    const modalEl = document.getElementById('customVendorDevicesModal');
    const titleEl = document.getElementById('vendor-modal-title');
    const tbody = document.getElementById('vendor-devices-table-body');

    if (titleEl) titleEl.innerText = vendorName;

    const filtered = allDevicesCache.filter(d => (d.vendor || '').toLowerCase() === vendorName.toLowerCase());

    if (tbody) {
        tbody.innerHTML = filtered.map(d => `
            <tr>
                <td class="fw-bold text-info">${escapeHtml(d.hostname)}</td>
                <td><code>${d.ip_address}</code></td>
                <td>${escapeHtml(d.model || '-')}</td>
                <td>${escapeHtml(d.os_version || '-')}</td>
                <td><small>${escapeHtml(d.location || '-')}</small></td>
                <td><span class="badge bg-success">${d.status}</span></td>
            </tr>
        `).join('') || `<tr><td colspan="6" class="text-center text-muted">No hay equipos registrados para ${vendorName}.</td></tr>`;
    }

    if (modalEl) modalEl.classList.remove('d-none');
}

function closeVendorDevicesModal() {
    const modalEl = document.getElementById('customVendorDevicesModal');
    if (modalEl) modalEl.classList.add('d-none');
}

// Ejecutar cuando toda la ventana y scripts CDN hayan cargado completamente
window.addEventListener('load', () => {
    updateClock();
    setInterval(updateClock, 1000);
    
    setupDateFilterLimits();
    checkNtpSync();
    setInterval(checkNtpSync, 30000);

    // Inicializar Modal de Login Obligatorio con verificación de seguridad
    const loginEl = document.getElementById('loginModal');
    if (loginEl) {
        if (typeof bootstrap !== 'undefined') {
            loginModalInstance = new bootstrap.Modal(loginEl);
            loginModalInstance.show();
        } else {
            console.warn("Bootstrap JS aún no está disponible. Mostrando formulario directo.");
            document.getElementById('app-content').classList.remove('d-none');
        }
    }

    setupFormListeners();
});

function updateClock() {
    const now = new Date();
    const clockEl = document.getElementById('clock');
    if (clockEl) clockEl.innerText = now.toLocaleTimeString();
}

function setupDateFilterLimits() {
    const today = new Date().toISOString().split('T')[0];
    const startDateInput = document.getElementById('filter-start-date');
    const endDateInput = document.getElementById('filter-end-date');

    if (startDateInput) startDateInput.setAttribute('max', today);
    if (endDateInput) endDateInput.setAttribute('max', today);
}

async function checkNtpSync() {
    const badge = document.getElementById('ntp-status-badge');
    try {
        const res = await fetch('/api/ntp/sync');
        const data = await res.json();

        if (data.in_sync) {
            badge.className = 'badge bg-success text-white small';
            badge.innerHTML = `<i class="fa-solid fa-check-double me-1"></i> NTP Sincronizado (${data.drift_seconds}s)`;
        } else {
            badge.className = 'badge bg-warning text-dark small';
            badge.innerHTML = `<i class="fa-solid fa-triangle-exclamation me-1"></i> Desfase NTP (${data.drift_seconds}s)`;
        }
    } catch (err) {
        if (badge) {
            badge.className = 'badge bg-secondary text-white small';
            badge.innerHTML = `<i class="fa-solid fa-clock me-1"></i> Modo Local`;
        }
    }
}

function showAlert(message, type = 'success') {
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        alertContainer.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show mb-3" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        setTimeout(() => { alertContainer.innerHTML = ''; }, 2500);
    }
}

function switchTab(tabName) {
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('d-none'));

    const activeTab = document.getElementById(`tab-${tabName}`);
    const activeView = document.getElementById(`view-${tabName}`);

    if (activeTab) activeTab.classList.add('active');
    if (activeView) activeView.classList.remove('d-none');

    if (tabName === 'dashboard') loadDashboardData();
    if (tabName === 'devices') loadDevices();
    if (tabName === 'syslog') loadSyslogEvents();
    if (tabName === 'incidents') loadIncidents();
}

async function loadDashboardData() {
    try {
        const [devRes, sysRes, incRes] = await Promise.all([
            fetch('/api/devices'),
            fetch('/api/syslog/events'),
            fetch('/api/incidents')
        ]);

        const devices = devRes.ok ? await devRes.json() : [];
        const events = sysRes.ok ? await sysRes.json() : [];
        const incidents = incRes.ok ? await incRes.json() : [];

        // Guardar respaldo en caché para las ventanas flotantes
        allDevicesCache = devices;
        allSyslogEventsCache = events;
        allIncidentsCache = incidents;

        // Contadores por fabricante
        const ciscoCount = devices.filter(d => (d.vendor || '').toLowerCase() === 'cisco').length;
        const fortiCount = devices.filter(d => (d.vendor || '').toLowerCase() === 'fortinet').length;
        const huaweiCount = devices.filter(d => (d.vendor || '').toLowerCase() === 'huawei').length;

        const elCisco = document.getElementById('stat-cisco-count');
        const elForti = document.getElementById('stat-fortinet-count');
        const elHuawei = document.getElementById('stat-huawei-count');

        if (elCisco) elCisco.innerText = ciscoCount;
        if (elForti) elForti.innerText = fortiCount;
        if (elHuawei) elHuawei.innerText = huaweiCount;

        // Contadores generales
        const elDev = document.getElementById('stat-devices-count');
        const elInc = document.getElementById('stat-incidents-count');
        const elCrit = document.getElementById('stat-critical-count');
        const elWarn = document.getElementById('stat-warning-count');

        if (elDev) elDev.innerText = devices.length;
        if (elInc) elInc.innerText = incidents.length;

        const criticals = events.filter(e => e.severity <= 3).length;
        const warnings = events.filter(e => e.severity === 4).length;
        const infos = events.filter(e => e.severity > 4).length;

        if (elCrit) elCrit.innerText = criticals;
        if (elWarn) elWarn.innerText = warnings;

        // Llenar tabla del Dashboard
        const recentBody = document.getElementById('dashboard-recent-events');
        if (recentBody) {
            recentBody.innerHTML = events.slice(0, 10).map(e => `
                <tr>
                    <td><small class="text-muted">${e.timestamp ? e.timestamp.replace('T', ' ').substring(0, 19) : 'N/A'}</small></td>
                    <td><code>${e.source_ip}</code></td>
                    <td><span class="badge badge-severity-${e.severity}">${e.severity_name} (${e.severity})</span></td>
                    <td class="text-truncate" style="max-width: 400px;">${escapeHtml(e.message)}</td>
                </tr>
            `).join('') || '<tr><td colspan="4" class="text-center text-muted">No hay eventos registrados.</td></tr>';
        }

        // Cargar gráficas si la librería existe
        if (typeof Chart !== 'undefined') {
            renderDashboardCharts(criticals, warnings, infos, events);
        }

    } catch (err) {
        console.error("Error al cargar datos del dashboard:", err);
    }
}

function renderDashboardCharts(criticals, warnings, infos, events) {
    // 1. Gráfica de Severidades (Dona)
    const ctxSev = document.getElementById('chart-severity');
    if (ctxSev) {
        if (severityChartInstance) severityChartInstance.destroy();
        severityChartInstance = new Chart(ctxSev, {
            type: 'doughnut',
            data: {
                labels: ['Críticos (0-3)', 'Advertencias (4)', 'Informativos (5-7)'],
                datasets: [{
                    data: [criticals, warnings, infos],
                    backgroundColor: ['#dc3545', '#ffc107', '#0dcaf0'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#0f172a', font: { size: 11, weight: 'bold' } } }
                }
            }
        });
    }

    // 2. Gráfica de Vendors (Barras)
    const ctxVen = document.getElementById('chart-vendors');
    if (ctxVen) {
        let ciscoCount = 0, fortiCount = 0, huaweiCount = 0;

        events.forEach(e => {
            const msg = (e.message || '').toUpperCase();
            if (msg.includes('CISCO')) ciscoCount++;
            else if (msg.includes('FORTI')) fortiCount++;
            else if (msg.includes('HUAWEI')) huaweiCount++;
        });

        const othersCount = Math.max(0, events.length - (ciscoCount + fortiCount + huaweiCount));

        if (vendorChartInstance) vendorChartInstance.destroy();
        vendorChartInstance = new Chart(ctxVen, {
            type: 'bar',
            data: {
                labels: ['Cisco', 'Fortinet', 'Huawei', 'Otros'],
                datasets: [{
                    label: 'Eventos',
                    data: [ciscoCount, fortiCount, huaweiCount, othersCount],
                    backgroundColor: ['#0d6efd', '#fd7e14', '#198754', '#6c757d']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { ticks: { color: '#0f172a', font: { weight: 'bold', size: 11 } } },
                    y: { ticks: { color: '#0f172a', font: { weight: 'bold', size: 11 }, precision: 0 } }
                }
            }
        });
    }
}

async function loadDevices() {
    try {
        const res = await fetch('/api/devices');
        if (!res.ok) throw new Error("Falla al consultar la API de dispositivos");
        const devices = await res.json();

        const tbody = document.getElementById('devices-table-body');
        tbody.innerHTML = devices.map(d => `
            <tr>
                <td class="fw-bold text-info">${escapeHtml(d.hostname)}</td>
                <td><code>${d.ip_address}</code></td>
                <td><span class="badge bg-secondary">${d.vendor}</span></td>
                <td>${escapeHtml(d.model || '-')}</td>
                <td>${escapeHtml(d.os_version || '-')}</td>
                <td><small>${escapeHtml(d.location || '-')}</small></td>
                <td><span class="badge bg-success">${d.status}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="7" class="text-center text-muted">No hay dispositivos en inventario.</td></tr>';

        const incDevSelect = document.getElementById('inc-device-id');
        if (incDevSelect) {
            incDevSelect.innerHTML = devices.map(d => `<option value="${d.id}">${d.hostname} (${d.ip_address})</option>`).join('');
        }

    } catch (err) {
        console.error(err);
        showAlert('Error al cargar inventario', 'danger');
    }
}

async function loadSyslogEvents() {
    try {
        let url = '/api/syslog/events?';
        if (currentSeverityFilter !== null) url += `severity=${currentSeverityFilter}&`;

        const startDate = document.getElementById('filter-start-date')?.value;
        const endDate = document.getElementById('filter-end-date')?.value;

        if (startDate && startDate.trim() !== "") url += `start_date=${startDate}&`;
        if (endDate && endDate.trim() !== "") url += `end_date=${endDate}&`;

        const res = await fetch(url);
        if (!res.ok) throw new Error("Error en la consulta de logs");
        const events = await res.json();

        const tbody = document.getElementById('syslog-table-body');
        tbody.innerHTML = events.map(e => `
            <tr>
                <td><small class="text-muted">#${e.id}</small></td>
                <td><small>${e.timestamp ? e.timestamp.replace('T', ' ').substring(0, 19) : '-'}</small></td>
                <td><code>${e.source_ip}</code></td>
                <td><span class="badge badge-severity-${e.severity}">${e.severity_name} (${e.severity})</span></td>
                <td><small class="font-monospace">${escapeHtml(e.message)}</small></td>
                <td>
                    ${e.severity <= 3 ? `<button class="btn btn-sm btn-outline-warning" onclick="convertEventToIncident(${e.id}, ${e.device_id}, '${escapeHtml(e.message)}')"><i class="fa-solid fa-file-circle-plus"></i> Crear Ticket</button>` : '-'}
                </td>
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No hay eventos para los filtros aplicados.</td></tr>';

    } catch (err) {
        console.error(err);
        showAlert('Error al cargar logs Syslog', 'danger');
    }
}

async function convertEventToIncident(eventId, deviceId, message) {
    if (!deviceId) {
        showAlert('No se puede crear ticket de un evento sin dispositivo asociado.', 'warning');
        return;
    }
    
    const title = `Incidente desde Alerta: ${message.substring(0, 50)}...`;
    const res = await fetch('/api/incidents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title: title,
            device_id: deviceId,
            event_id: eventId,
            priority: 'Critical',
            assignee: 'Operador NOC',
            root_cause: `Derivado automáticamente del evento Syslog #${eventId}`
        })
    });

    if (res.ok) {
        showAlert(`Incidente ticket derivado con éxito del evento #${eventId}`, 'success');
        loadDashboardData();
    } else {
        showAlert('Error al convertir evento a incidente', 'danger');
    }
}

function filterSyslogBySeverity(sev, btn) {
    document.querySelectorAll('#view-syslog .btn-group .btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentSeverityFilter = sev;
    loadSyslogEvents();
}

function applyDateFilters() {
    const today = new Date().toISOString().split('T')[0];
    const endDateInput = document.getElementById('filter-end-date');

    if (endDateInput && endDateInput.value && endDateInput.value > today) {
        showAlert('No se pueden seleccionar fechas futuras. Se ajustó a la fecha de hoy.', 'warning');
        endDateInput.value = today;
    }

    loadSyslogEvents();
}

async function loadIncidents() {
    try {
        const res = await fetch('/api/incidents');
        if (!res.ok) throw new Error("Falla al consultar incidentes");
        const incidents = await res.json();

        const tbody = document.getElementById('incidents-table-body');
        tbody.innerHTML = incidents.map(i => `
            <tr>
                <td><small class="text-muted">#${i.id}</small></td>
                <td class="fw-bold">${escapeHtml(i.title)}</td>
                <td><span class="badge bg-secondary">${escapeHtml(i.device_hostname)}</span></td>
                <td><span class="badge bg-${i.priority === 'Critical' ? 'danger' : 'warning'}">${i.priority}</span></td>
                <td><span class="badge bg-info">${i.status}</span></td>
                <td><small>${escapeHtml(i.assignee)}</small></td>
                <td><small class="text-muted">${escapeHtml(i.root_cause || '-')}</small></td>
            </tr>
        `).join('') || '<tr><td colspan="7" class="text-center text-muted">No hay incidentes creados.</td></tr>';

    } catch (err) {
        console.error(err);
        showAlert('Error al cargar incidentes', 'danger');
    }
}

function setupFormListeners() {
    // Formulario Login
    const formLogin = document.getElementById('form-login');
    if (formLogin) {
        formLogin.addEventListener('submit', async (e) => {
            e.preventDefault();
            const cc_number = document.getElementById('login-cc').value.trim();
            const password = document.getElementById('login-password').value;

            // Validación de Cédula (Solo Dígitos)
            if (!/^\d+$/.test(cc_number)) {
                showAlert('La Cédula de Ciudadanía (CC) debe ser un número entero sin puntos ni letras.', 'warning');
                return;
            }

            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cc_number, password })
            });

            const data = await res.json();
            if (res.ok) {
                if (loginModalInstance) loginModalInstance.hide();
                document.getElementById('app-content').classList.remove('d-none');
                document.getElementById('user-display-cc').innerText = data.user.cc_number;
                showAlert(`¡Bienvenido/a ${data.user.full_name}! Acceso autenticado.`);
                loadDashboardData();
            } else {
                showAlert(data.error || 'Credenciales de acceso incorrectas', 'danger');
            }
        });
    }

    // Formulario Simulación Personalizada
    const formSim = document.getElementById('form-simulate-failures');
    if (formSim) {
        formSim.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fail_type = document.getElementById('sim-fail-type').value;
            const vendor = document.getElementById('sim-vendor').value;
            const severity = parseInt(document.getElementById('sim-severity').value);
            const count = parseInt(document.getElementById('sim-count').value);

            const res = await fetch('/api/syslog/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fail_type, vendor, severity, count })
            });

            const data = await res.json();
            if (res.ok) {
                closeSimulateModal();
                showAlert('Falla(s) creada(s) satisfactoriamente', 'success');

                loadDashboardData();
                loadSyslogEvents();
            } else {
                showAlert('Error al generar la simulación', 'danger');
            }
        });
    }

    // Formulario Agregar Dispositivo
    const formAddDev = document.getElementById('form-add-device');
    if (formAddDev) {
        formAddDev.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                hostname: document.getElementById('dev-hostname').value,
                ip_address: document.getElementById('dev-ip').value,
                vendor: document.getElementById('dev-vendor').value,
                model: document.getElementById('dev-model').value,
                os_version: document.getElementById('dev-os').value,
                location: document.getElementById('dev-location').value
            };

            const res = await fetch('/api/devices', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                closeAddDeviceModal();
                e.target.reset();
                showAlert('Dispositivo registrado con éxito en el inventario', 'success');
                loadDevices();
                loadDashboardData();
            } else {
                const err = await res.json();
                showAlert(err.error || 'Falla al guardar dispositivo', 'danger');
            }
        });
    }

    const formImportSys = document.getElementById('form-import-syslog');
    if (formImportSys) {
        formImportSys.addEventListener('submit', async (e) => {
            e.preventDefault();
            const logs = document.getElementById('syslog-raw-text').value;

            const res = await fetch('/api/syslog/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ logs })
            });

            if (res.ok) {
                const impModal = bootstrap.Modal.getInstance(document.getElementById('importSyslogModal'));
                if (impModal) impModal.hide();
                e.target.reset();
                showAlert('Logs procesados e importados correctamente');
                loadSyslogEvents();
                loadDashboardData();
            } else {
                showAlert('Error al procesar archivo de log', 'danger');
            }
        });
    }

    const formAddInc = document.getElementById('form-add-incident');
    if (formAddInc) {
        formAddInc.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                title: document.getElementById('inc-title').value,
                device_id: parseInt(document.getElementById('inc-device-id').value),
                priority: document.getElementById('inc-priority').value,
                assignee: document.getElementById('inc-assignee').value,
                root_cause: document.getElementById('inc-root-cause').value
            };

            const res = await fetch('/api/incidents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                closeAddIncidentModal();
                e.target.reset();
                showAlert('Incidente registrado correctamente', 'success');
                loadIncidents();
                loadDashboardData();
            } else {
                showAlert('Error al guardar el incidente', 'danger');
            }
        });
    }

    const formGen = document.getElementById('form-generate-template');
    if (formGen) {
        formGen.addEventListener('submit', async (e) => {
            e.preventDefault();
            const vendor = document.getElementById('gen-vendor').value;
            const syslog_ip = document.getElementById('gen-ip').value;

            const res = await fetch('/api/templates/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vendor, syslog_ip })
            });

            const data = await res.json();
            if (res.ok) {
                document.getElementById('template-output').innerText = data.configuration;
            } else {
                showAlert(data.error || 'Error al generar plantilla', 'danger');
            }
        });
    }

    const formConsole = document.getElementById('form-console-input');
    if (formConsole) {
        formConsole.addEventListener('submit', async (e) => {
            e.preventDefault();
            const vendor = document.getElementById('console-vendor').value;
            const cmdInput = document.getElementById('console-cmd');
            const command = cmdInput.value;

            const term = document.getElementById('terminal-screen');
            term.innerHTML += `<div class="text-warning mt-2">admin@${vendor}> ${escapeHtml(command)}</div>`;

            const res = await fetch('/api/console/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vendor, command })
            });

            const data = await res.json();
            if (data.success) {
                term.innerHTML += `<pre class="text-light mb-0">${escapeHtml(data.output)}</pre>`;
            } else {
                term.innerHTML += `<pre class="text-danger mb-0">${escapeHtml(data.output)}</pre>`;
            }

            cmdInput.value = '';
            term.scrollTop = term.scrollHeight;
        });
    }
}

function copyTemplate() {
    const text = document.getElementById('template-output').innerText;
    navigator.clipboard.writeText(text);
    showAlert('Plantilla copiada al portapapeles');
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function openAddDeviceModal() {
    const el = document.getElementById('customAddDeviceModal');
    if (el) el.classList.remove('d-none');
}

function closeAddDeviceModal() {
    const el = document.getElementById('customAddDeviceModal');
    if (el) el.classList.add('d-none');
}

function openSimulateModal() {
    const el = document.getElementById('customSimulateModal');
    if (el) el.classList.remove('d-none');
}

function closeSimulateModal() {
    const el = document.getElementById('customSimulateModal');
    if (el) el.classList.add('d-none');
}

function openAddIncidentModal() {
    const el = document.getElementById('customAddIncidentModal');
    if (el) el.classList.remove('d-none');
}

function closeAddIncidentModal() {
    const el = document.getElementById('customAddIncidentModal');
    if (el) el.classList.add('d-none');
}