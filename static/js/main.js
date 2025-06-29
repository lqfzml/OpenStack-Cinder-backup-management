// 全局变量
let volumes = [];
let backups = { full_backups: [], incremental_backups: [], all_backups: [] };
let schedules = [];
let serverSnapshots = [];
let volumeSnapshots = [];
let servers = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    checkHealth();
    loadData();
    
    // 定期刷新数据
    setInterval(loadData, 30000); // 每30秒刷新一次
});

// 检查系统健康状态
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        const statusBar = document.getElementById('statusBar');
        const statusText = document.getElementById('statusText');
        
        if (data.status === 'healthy') {
            statusBar.className = 'alert alert-success';
            statusText.innerHTML = `<i class="bi bi-check-circle"></i> 系统正常 - OpenStack已连接，共 ${data.volume_count} 个云硬盘`;
        } else {
            statusBar.className = 'alert alert-danger';
            statusText.innerHTML = `<i class="bi bi-exclamation-triangle"></i> 系统异常 - ${data.error}`;
        }
    } catch (error) {
        console.error('健康检查失败:', error);
        const statusBar = document.getElementById('statusBar');
        const statusText = document.getElementById('statusText');
        statusBar.className = 'alert alert-danger';
        statusText.innerHTML = '<i class="bi bi-exclamation-triangle"></i> 无法连接到服务器';
    }
}

// 加载数据
async function loadData() {
    await Promise.all([
        loadVolumes(),
        loadBackups(),
        loadSchedules(),
        loadServerSnapshots(),
        loadVolumeSnapshots(),
        loadServers()
    ]);
}

// 加载云硬盘列表
async function loadVolumes() {
    try {
        showLoading(true);
        const response = await fetch('/api/volumes');
        volumes = await response.json();
        renderVolumesTable();
    } catch (error) {
        console.error('加载云硬盘失败:', error);
        showMessage('错误', '加载云硬盘列表失败: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// 加载备份列表
async function loadBackups() {
    try {
        const response = await fetch('/api/backups');
        backups = await response.json();
        renderBackupsTables();
    } catch (error) {
        console.error('加载备份失败:', error);
        showMessage('错误', '加载备份列表失败: ' + error.message);
    }
}

// 加载定时备份列表
async function loadSchedules() {
    try {
        const response = await fetch('/api/schedules');
        schedules = await response.json();
        renderSchedulesTable();
    } catch (error) {
        console.error('加载定时备份失败:', error);
        showMessage('错误', '加载定时备份列表失败: ' + error.message);
    }
}

// 加载云主机快照列表
async function loadServerSnapshots() {
    try {
        const response = await fetch('/api/server-snapshots');
        serverSnapshots = await response.json();
        renderServerSnapshotsTable();
    } catch (error) {
        console.error('加载云主机快照列表失败:', error);
        showMessage('错误', '加载云主机快照列表失败: ' + error.message);
    }
}

// 加载云硬盘快照列表
async function loadVolumeSnapshots() {
    try {
        const response = await fetch('/api/volume-snapshots');
        volumeSnapshots = await response.json();
        renderVolumeSnapshotsTable();
    } catch (error) {
        console.error('加载云硬盘快照列表失败:', error);
        showMessage('错误', '加载云硬盘快照列表失败: ' + error.message);
    }
}

// 加载云主机列表
async function loadServers() {
    try {
        const response = await fetch('/api/servers');
        servers = await response.json();
    } catch (error) {
        console.error('加载云主机列表失败:', error);
    }
}

// 渲染云硬盘表格
function renderVolumesTable() {
    const tbody = document.getElementById('volumesTableBody');
    
    if (volumes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">暂无云硬盘</td></tr>';
        return;
    }
    
    tbody.innerHTML = volumes.map(volume => `
        <tr>
            <td>
                <input type="checkbox" class="volume-checkbox" value="${volume.id}" 
                       ${volume.backupable ? '' : 'disabled'}>
            </td>
            <td><code>${volume.id}</code></td>
            <td>${volume.name || '未命名'}</td>
            <td>${volume.size}</td>
            <td>
                <span class="badge bg-${getStatusColor(volume.status)}">
                    ${volume.status}
                    ${volume.backupable ? '<i class="bi bi-check-circle ms-1"></i>' : ''}
                </span>
            </td>
            <td>${formatDateTime(volume.created_at)}</td>
        </tr>
    `).join('');
}

// 渲染备份表格 - 分离全量备份和增量备份
function renderBackupsTables() {
    // 渲染全量备份表格
    const fullTbody = document.getElementById('fullBackupsTableBody');
    if (backups.full_backups && backups.full_backups.length === 0) {
        fullTbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无全量备份</td></tr>';
    } else {
        fullTbody.innerHTML = backups.full_backups.map(backup => `
            <tr class="backup-full">
                <td><code>${backup.id}</code></td>
                <td>${backup.name || '未命名'}</td>
                <td><code>${backup.volume_id}</code></td>
                <td>${backup.size || '未知'}</td>
                <td>
                    <span class="badge bg-${getStatusColor(backup.status)}">
                        ${backup.status}
                    </span>
                </td>
                <td>${formatDateTime(backup.created_at)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="deleteBackup('${backup.id}')" 
                            ${backup.status === 'available' ? '' : 'disabled'}>
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    // 渲染增量备份表格
    const incrementalTbody = document.getElementById('incrementalBackupsTableBody');
    if (backups.incremental_backups && backups.incremental_backups.length === 0) {
        incrementalTbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无增量备份</td></tr>';
    } else {
        incrementalTbody.innerHTML = backups.incremental_backups.map(backup => `
            <tr class="backup-incremental">
                <td><code>${backup.id}</code></td>
                <td>${backup.name || '未命名'}</td>
                <td><code>${backup.volume_id}</code></td>
                <td>${backup.size || '未知'}</td>
                <td>
                    <span class="badge bg-${getStatusColor(backup.status)}">
                        ${backup.status}
                    </span>
                </td>
                <td>${formatDateTime(backup.created_at)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="deleteBackup('${backup.id}')" 
                            ${backup.status === 'available' ? '' : 'disabled'}>
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
}

// 渲染定时备份表格
function renderSchedulesTable() {
    const tbody = document.getElementById('schedulesTableBody');
    if (schedules.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无定时备份</td></tr>';
        return;
    }

    tbody.innerHTML = schedules.map(schedule => {
        const volumeCount = schedule.volume_ids ? schedule.volume_ids.length : 0;
        const statusClass = schedule.enabled ? 'schedule-enabled' : 'schedule-disabled';
        const statusText = schedule.enabled ? '启用' : '禁用';
        
        return `
            <tr>
                <td>${schedule.name || '未命名'}</td>
                <td>${schedule.backup_type === 'full' ? '全量备份' : '增量备份'}</td>
                <td>${volumeCount}</td>
                <td>${schedule.schedule_type === 'daily' ? '每日' : '每周'} ${schedule.schedule_time}</td>
                <td><span class="${statusClass}">${statusText}</span></td>
                <td>${formatDateTime(schedule.created_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-primary" onclick="toggleSchedule('${schedule.id}')">
                            <i class="bi bi-${schedule.enabled ? 'pause' : 'play'}"></i>
                        </button>
                        <button type="button" class="btn btn-outline-info" onclick="manageScheduleVolumes('${schedule.id}')">
                            <i class="bi bi-gear"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger" onclick="deleteSchedule('${schedule.id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// 渲染云主机快照表格
function renderServerSnapshotsTable() {
    const tbody = document.getElementById('serverSnapshotsTableBody');
    if (serverSnapshots.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无云主机快照</td></tr>';
        return;
    }

    tbody.innerHTML = serverSnapshots.map(snapshot => {
        const statusClass = getStatusClass(snapshot.status);
        return `
            <tr>
                <td>${snapshot.id}</td>
                <td>${snapshot.name || '未命名'}</td>
                <td>${snapshot.server_id}</td>
                <td>${snapshot.size || 0}</td>
                <td><span class="${statusClass}">${snapshot.status}</span></td>
                <td>${formatDateTime(snapshot.created_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-danger" onclick="deleteServerSnapshot('${snapshot.id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// 渲染云硬盘快照表格
function renderVolumeSnapshotsTable() {
    const tbody = document.getElementById('volumeSnapshotsTableBody');
    if (volumeSnapshots.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无云硬盘快照</td></tr>';
        return;
    }

    tbody.innerHTML = volumeSnapshots.map(snapshot => {
        const statusClass = getStatusClass(snapshot.status);
        return `
            <tr>
                <td>${snapshot.id}</td>
                <td>${snapshot.name || '未命名'}</td>
                <td>${snapshot.volume_id}</td>
                <td>${snapshot.size || 0}</td>
                <td><span class="${statusClass}">${snapshot.status}</span></td>
                <td>${formatDateTime(snapshot.created_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-danger" onclick="deleteVolumeSnapshot('${snapshot.id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// 创建备份
async function createBackup(type) {
    const selectedVolumes = getSelectedVolumes();
    
    if (selectedVolumes.length === 0) {
        showMessage('警告', '请先选择要备份的云硬盘');
        return;
    }
    
    const backupName = prompt(`请输入${type === 'full' ? '全量' : '增量'}备份名称（可选）:`);
    
    try {
        showLoading(true);
        const response = await fetch(`/api/backup/${type}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                volume_ids: selectedVolumes,
                name: backupName || undefined
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('成功', result.message);
            // 清空选择
            clearVolumeSelection();
            // 刷新数据
            setTimeout(loadData, 2000);
        } else {
            showMessage('错误', result.error || '备份创建失败');
        }
    } catch (error) {
        console.error('创建备份失败:', error);
        showMessage('错误', '创建备份失败: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// 显示定时备份模态框
function showScheduleModal() {
    // 加载云硬盘列表到模态框
    loadScheduleVolumes();
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('scheduleModal'));
    modal.show();
}

// 加载定时备份的云硬盘列表
function loadScheduleVolumes() {
    const container = document.getElementById('scheduleVolumeList');
    
    if (volumes.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">暂无可用云硬盘</div>';
        return;
    }
    
    // 过滤出可备份的云硬盘
    const backupableVolumes = volumes.filter(volume => volume.backupable);
    
    if (backupableVolumes.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">暂无可备份的云硬盘</div>';
        return;
    }
    
    container.innerHTML = backupableVolumes.map(volume => `
        <div class="form-check">
            <input class="form-check-input schedule-volume-checkbox" type="checkbox" 
                   value="${volume.id}" id="schedule_volume_${volume.id}">
            <label class="form-check-label" for="schedule_volume_${volume.id}">
                ${volume.name || '未命名'} (${volume.id}) - ${volume.size}GB - 
                <span class="badge bg-${getStatusColor(volume.status)}">${volume.status}</span>
            </label>
        </div>
    `).join('');
}

// 切换星期选择显示
function toggleWeekdays() {
    const scheduleType = document.getElementById('scheduleType').value;
    const weekdaysSection = document.getElementById('weekdaysSection');
    
    if (scheduleType === 'weekly') {
        weekdaysSection.style.display = 'block';
    } else {
        weekdaysSection.style.display = 'none';
    }
}

// 创建定时备份
async function createSchedule() {
    const name = document.getElementById('scheduleName').value;
    const backupType = document.getElementById('backupType').value;
    const scheduleType = document.getElementById('scheduleType').value;
    const scheduleTime = document.getElementById('scheduleTime').value;
    
    // 获取选中的云硬盘
    const selectedVolumes = Array.from(document.querySelectorAll('.schedule-volume-checkbox:checked'))
        .map(cb => cb.value);
    
    if (selectedVolumes.length === 0) {
        showMessage('警告', '请选择要备份的云硬盘');
        return;
    }
    
    // 获取选中的星期
    let weekdays = [];
    if (scheduleType === 'weekly') {
        weekdays = Array.from(document.querySelectorAll('.weekday-checkbox:checked'))
            .map(cb => parseInt(cb.value));
        
        if (weekdays.length === 0) {
            showMessage('警告', '请选择备份的星期');
            return;
        }
    }
    
    try {
        showLoading(true);
        const response = await fetch('/api/schedules', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                volume_ids: selectedVolumes,
                backup_type: backupType,
                schedule_type: scheduleType,
                schedule_time: scheduleTime,
                weekdays: weekdays,
                name: name
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('成功', result.message);
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('scheduleModal'));
            modal.hide();
            // 刷新数据
            setTimeout(loadData, 1000);
        } else {
            showMessage('错误', result.error || '创建定时备份失败');
        }
    } catch (error) {
        console.error('创建定时备份失败:', error);
        showMessage('错误', '创建定时备份失败: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// 切换定时备份状态
async function toggleSchedule(scheduleId) {
    try {
        const response = await fetch(`/api/schedules/${scheduleId}/toggle`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('成功', result.message);
            setTimeout(loadData, 1000);
        } else {
            showMessage('错误', result.error || '切换状态失败');
        }
    } catch (error) {
        console.error('切换定时备份状态失败:', error);
        showMessage('错误', '切换状态失败: ' + error.message);
    }
}

// 删除定时备份
async function deleteSchedule(scheduleId) {
    if (!confirm('确定要删除这个定时备份吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/schedules/${scheduleId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('成功', result.message);
            setTimeout(loadData, 1000);
        } else {
            showMessage('错误', result.error || '删除失败');
        }
    } catch (error) {
        console.error('删除定时备份失败:', error);
        showMessage('错误', '删除失败: ' + error.message);
    }
}

// 清理备份（支持自定义天数和按云硬盘策略）
async function cleanupBackups() {
    const cleanupMode = document.querySelector('input[name="cleanupMode"]:checked').value;
    
    if (cleanupMode === 'global') {
        // 统一清理策略
        const retentionDays = document.getElementById('retentionDays').value;
        
        if (!retentionDays || retentionDays < 1 || retentionDays > 365) {
            showMessage('错误', '请输入有效的保留天数（1-365天）');
            return;
        }
        
        if (!confirm(`确定要删除超过 ${retentionDays} 天的备份吗？此操作无法恢复！`)) {
            return;
        }
        
        try {
            showLoading(true);
            const response = await fetch('/api/backup/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ retention_days: parseInt(retentionDays) })
            });
            
            const result = await response.json();
            
            if (result.success) {
                showMessage('成功', result.message);
                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('cleanupModal'));
                modal.hide();
                setTimeout(loadData, 2000);
            } else {
                showMessage('错误', result.error || '备份清理失败');
            }
        } catch (error) {
            console.error('备份清理失败:', error);
            showMessage('错误', '备份清理失败: ' + error.message);
        } finally {
            showLoading(false);
        }
    } else {
        // 按云硬盘策略
        const volumePolicies = {};
        let hasValidPolicy = false;
        
        document.querySelectorAll('.volume-retention-days').forEach(input => {
            const volumeId = input.dataset.volumeId;
            const days = parseInt(input.value);
            
            if (days && days >= 1 && days <= 365) {
                volumePolicies[volumeId] = days;
                hasValidPolicy = true;
            }
        });
        
        if (!hasValidPolicy) {
            showMessage('错误', '请至少为一个云硬盘设置有效的保留天数（1-365天）');
            return;
        }
        
        const policySummary = Object.entries(volumePolicies)
            .map(([volumeId, days]) => `云硬盘 ${volumeId}: ${days}天`)
            .join('; ');
        
        if (!confirm(`确定要按以下策略清理备份吗？\n${policySummary}\n\n此操作无法恢复！`)) {
            return;
        }
        
        try {
            showLoading(true);
            const response = await fetch('/api/backup/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ volume_policies: volumePolicies })
            });
            
            const result = await response.json();
            
            if (result.success) {
                showMessage('成功', result.message);
                // 关闭模态框
                const modal = bootstrap.Modal.getInstance(document.getElementById('cleanupModal'));
                modal.hide();
                setTimeout(loadData, 2000);
            } else {
                showMessage('错误', result.error || '备份清理失败');
            }
        } catch (error) {
            console.error('备份清理失败:', error);
            showMessage('错误', '备份清理失败: ' + error.message);
        } finally {
            showLoading(false);
        }
    }
}

// 显示清理备份模态框
function showCleanupModal() {
    const modal = new bootstrap.Modal(document.getElementById('cleanupModal'));
    modal.show();
    
    // 加载云硬盘列表用于按云硬盘策略
    loadVolumePoliciesList();
    
    // 绑定清理模式切换事件
    document.querySelectorAll('input[name="cleanupMode"]').forEach(radio => {
        radio.addEventListener('change', toggleCleanupMode);
    });
}

// 切换清理模式
function toggleCleanupMode() {
    const globalSection = document.getElementById('globalCleanupSection');
    const volumeSection = document.getElementById('volumeCleanupSection');
    
    if (document.getElementById('cleanupModeGlobal').checked) {
        globalSection.style.display = 'block';
        volumeSection.style.display = 'none';
    } else {
        globalSection.style.display = 'none';
        volumeSection.style.display = 'block';
    }
}

// 加载云硬盘策略列表
async function loadVolumePoliciesList() {
    try {
        const volumePoliciesList = document.getElementById('volumePoliciesList');
        
        if (volumes.length === 0) {
            volumePoliciesList.innerHTML = '<div class="text-center text-muted">暂无云硬盘</div>';
            return;
        }
        
        // 获取有备份的云硬盘
        const volumesWithBackups = new Set();
        backups.all_backups.forEach(backup => {
            volumesWithBackups.add(backup.volume_id);
        });
        
        if (volumesWithBackups.size === 0) {
            volumePoliciesList.innerHTML = '<div class="text-center text-muted">暂无备份的云硬盘</div>';
            return;
        }
        
        volumePoliciesList.innerHTML = Array.from(volumesWithBackups).map(volumeId => {
            const volume = volumes.find(v => v.id === volumeId);
            const volumeName = volume ? volume.name || '未命名' : '未知';
            const backupCount = backups.all_backups.filter(b => b.volume_id === volumeId).length;
            
            return `
                <div class="row mb-2 align-items-center">
                    <div class="col-md-6">
                        <strong>${volumeName}</strong> (${volumeId})
                        <br><small class="text-muted">${backupCount} 个备份</small>
                    </div>
                    <div class="col-md-6">
                        <div class="input-group input-group-sm">
                            <input type="number" class="form-control volume-retention-days" 
                                   data-volume-id="${volumeId}" 
                                   value="30" min="1" max="365" 
                                   placeholder="保留天数">
                            <span class="input-group-text">天</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('加载云硬盘策略列表失败:', error);
        document.getElementById('volumePoliciesList').innerHTML = 
            '<div class="text-center text-danger">加载失败: ' + error.message + '</div>';
    }
}

// 全局变量存储当前管理的定时备份ID
let currentManageScheduleId = null;

// 显示定时备份管理模态框
async function manageScheduleVolumes(scheduleId) {
    currentManageScheduleId = scheduleId;
    const modal = new bootstrap.Modal(document.getElementById('scheduleManageModal'));
    modal.show();
    
    // 加载云硬盘列表
    await loadScheduleManageVolumes();
}

// 加载定时备份管理的云硬盘列表
async function loadScheduleManageVolumes() {
    try {
        const schedule = schedules.find(s => s.id === currentManageScheduleId);
        if (!schedule) {
            showMessage('错误', '定时备份不存在');
            return;
        }
        
        // 渲染当前云硬盘列表
        const currentVolumesList = document.getElementById('currentVolumesList');
        if (schedule.volume_ids.length === 0) {
            currentVolumesList.innerHTML = '<div class="text-center text-muted">暂无云硬盘</div>';
        } else {
            const currentVolumes = volumes.filter(v => schedule.volume_ids.includes(v.id));
            currentVolumesList.innerHTML = currentVolumes.map(volume => `
                <div class="form-check">
                    <input class="form-check-input current-volume-checkbox" type="checkbox" value="${volume.id}" id="current_${volume.id}">
                    <label class="form-check-label" for="current_${volume.id}">
                        <strong>${volume.name || '未命名'}</strong> (${volume.id})
                        <br><small class="text-muted">${volume.size}GB - ${volume.status}</small>
                    </label>
                </div>
            `).join('');
        }
        
        // 渲染可添加的云硬盘列表
        const availableVolumesList = document.getElementById('availableVolumesList');
        const availableVolumes = volumes.filter(v => !schedule.volume_ids.includes(v.id) && v.backupable);
        
        if (availableVolumes.length === 0) {
            availableVolumesList.innerHTML = '<div class="text-center text-muted">暂无可添加的云硬盘</div>';
        } else {
            availableVolumesList.innerHTML = availableVolumes.map(volume => `
                <div class="form-check">
                    <input class="form-check-input available-volume-checkbox" type="checkbox" value="${volume.id}" id="available_${volume.id}">
                    <label class="form-check-label" for="available_${volume.id}">
                        <strong>${volume.name || '未命名'}</strong> (${volume.id})
                        <br><small class="text-muted">${volume.size}GB - ${volume.status}</small>
                    </label>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('加载定时备份管理云硬盘失败:', error);
        showMessage('错误', '加载云硬盘列表失败: ' + error.message);
    }
}

// 添加云硬盘到定时备份
async function addVolumesToSchedule() {
    const selectedVolumes = Array.from(document.querySelectorAll('.available-volume-checkbox:checked'))
        .map(cb => cb.value);
    
    if (selectedVolumes.length === 0) {
        showMessage('错误', '请选择要添加的云硬盘');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`/api/schedules/${currentManageScheduleId}/volumes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ volume_ids: selectedVolumes })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('成功', result.message);
            // 刷新数据并重新加载管理界面
            await loadData();
            await loadScheduleManageVolumes();
        } else {
            showMessage('错误', result.error || '添加云硬盘失败');
        }
    } catch (error) {
        console.error('添加云硬盘失败:', error);
        showMessage('错误', '添加云硬盘失败: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// 从定时备份移除云硬盘
async function removeVolumesFromSchedule() {
    const selectedVolumes = Array.from(document.querySelectorAll('.current-volume-checkbox:checked'))
        .map(cb => cb.value);
    
    if (selectedVolumes.length === 0) {
        showMessage('错误', '请选择要移除的云硬盘');
        return;
    }
    
    if (!confirm(`确定要从定时备份中移除 ${selectedVolumes.length} 个云硬盘吗？`)) {
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`/api/schedules/${currentManageScheduleId}/volumes`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ volume_ids: selectedVolumes })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('成功', result.message);
            // 刷新数据并重新加载管理界面
            await loadData();
            await loadScheduleManageVolumes();
        } else {
            showMessage('错误', result.error || '移除云硬盘失败');
        }
    } catch (error) {
        console.error('移除云硬盘失败:', error);
        showMessage('错误', '移除云硬盘失败: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// 删除备份
async function deleteBackup(backupId) {
    if (!confirm('确定要删除这个备份吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/backup/${backupId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('成功', result.message);
            setTimeout(loadData, 1000);
        } else {
            showMessage('错误', result.error || '删除失败');
        }
    } catch (error) {
        console.error('删除备份失败:', error);
        showMessage('错误', '删除失败: ' + error.message);
    }
}

// 刷新数据
function refreshData() {
    loadData();
}

// 获取选中的云硬盘
function getSelectedVolumes() {
    return Array.from(document.querySelectorAll('.volume-checkbox:checked'))
        .map(cb => cb.value);
}

// 清空云硬盘选择
function clearVolumeSelection() {
    document.querySelectorAll('.volume-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('selectAllVolumes').checked = false;
}

// 全选/取消全选
function toggleSelectAll(type) {
    const selectAll = document.getElementById(`selectAll${type.charAt(0).toUpperCase() + type.slice(1)}`);
    const checkboxes = document.querySelectorAll(`.${type}-checkbox`);
    
    checkboxes.forEach(cb => {
        if (!cb.disabled) {
            cb.checked = selectAll.checked;
        }
    });
}

// 获取状态颜色
function getStatusColor(status) {
    switch (status) {
        case 'available':
        case 'available':
            return 'success';
        case 'in-use':
            return 'primary';
        case 'error':
            return 'danger';
        case 'creating':
            return 'warning';
        case 'deleting':
            return 'secondary';
        default:
            return 'secondary';
    }
}

// 格式化日期时间
function formatDateTime(dateString) {
    if (!dateString) return '未知';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 格式化定时备份时间
function formatScheduleTime(schedule) {
    let timeStr = schedule.schedule_time;
    
    if (schedule.schedule_type === 'weekly' && schedule.weekdays && schedule.weekdays.length > 0) {
        const weekdays = schedule.weekdays.map(day => {
            const days = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日'];
            return days[day];
        }).join('、');
        return `${weekdays} ${timeStr}`;
    } else {
        return `每日 ${timeStr}`;
    }
}

// 显示/隐藏加载动画
function showLoading(show) {
    const loading = document.getElementById('loading');
    loading.style.display = show ? 'flex' : 'none';
}

// 显示消息
function showMessage(title, message) {
    const modal = new bootstrap.Modal(document.getElementById('messageModal'));
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').textContent = message;
    modal.show();
}

// 显示快照清理模态框
function showSnapshotCleanupModal() {
    const modal = new bootstrap.Modal(document.getElementById('snapshotCleanupModal'));
    modal.show();
}

// 创建云主机快照
function createServerSnapshot() {
    // 加载云主机列表到模态框
    const serverList = document.getElementById('serverSnapshotList');
    if (servers.length === 0) {
        serverList.innerHTML = '<div class="text-center text-muted">暂无云主机</div>';
    } else {
        serverList.innerHTML = servers.map(server => `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${server.id}" id="server_${server.id}">
                <label class="form-check-label" for="server_${server.id}">
                    ${server.name} (${server.id}) - ${server.status}
                </label>
            </div>
        `).join('');
    }
    
    const modal = new bootstrap.Modal(document.getElementById('serverSnapshotModal'));
    modal.show();
}

// 确认创建云主机快照
function createServerSnapshotConfirm() {
    const selectedServers = Array.from(document.querySelectorAll('#serverSnapshotList input:checked'))
        .map(input => input.value);
    
    if (selectedServers.length === 0) {
        showMessage('错误', '请选择要创建快照的云主机');
        return;
    }
    
    const name = document.getElementById('serverSnapshotName').value;
    const description = document.getElementById('serverSnapshotDescription').value;
    
    showLoading();
    
    fetch('/api/server-snapshots', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            server_ids: selectedServers,
            name: name,
            description: description
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showMessage('成功', data.message);
            bootstrap.Modal.getInstance(document.getElementById('serverSnapshotModal')).hide();
            refreshData();
        } else {
            showMessage('错误', data.error || '创建云主机快照失败');
        }
    })
    .catch(error => {
        hideLoading();
        showMessage('错误', '创建云主机快照失败: ' + error.message);
    });
}

// 创建云硬盘快照
function createVolumeSnapshot() {
    // 加载云硬盘列表到模态框
    const volumeList = document.getElementById('volumeSnapshotList');
    if (volumes.length === 0) {
        volumeList.innerHTML = '<div class="text-center text-muted">暂无云硬盘</div>';
    } else {
        volumeList.innerHTML = volumes.map(volume => `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${volume.id}" id="volume_${volume.id}">
                <label class="form-check-label" for="volume_${volume.id}">
                    ${volume.name} (${volume.id}) - ${volume.size}GB - ${volume.status}
                </label>
            </div>
        `).join('');
    }
    
    const modal = new bootstrap.Modal(document.getElementById('volumeSnapshotModal'));
    modal.show();
}

// 确认创建云硬盘快照
function createVolumeSnapshotConfirm() {
    const selectedVolumes = Array.from(document.querySelectorAll('#volumeSnapshotList input:checked'))
        .map(input => input.value);
    
    if (selectedVolumes.length === 0) {
        showMessage('错误', '请选择要创建快照的云硬盘');
        return;
    }
    
    const name = document.getElementById('volumeSnapshotName').value;
    const description = document.getElementById('volumeSnapshotDescription').value;
    const force = document.getElementById('volumeSnapshotForce').checked;
    
    showLoading();
    
    fetch('/api/volume-snapshots', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            volume_ids: selectedVolumes,
            name: name,
            description: description,
            force: force
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showMessage('成功', data.message);
            bootstrap.Modal.getInstance(document.getElementById('volumeSnapshotModal')).hide();
            refreshData();
        } else {
            showMessage('错误', data.error || '创建云硬盘快照失败');
        }
    })
    .catch(error => {
        hideLoading();
        showMessage('错误', '创建云硬盘快照失败: ' + error.message);
    });
}

// 删除云主机快照
function deleteServerSnapshot(snapshotId) {
    if (!confirm('确定要删除这个云主机快照吗？此操作不可恢复。')) {
        return;
    }
    
    showLoading();
    
    fetch(`/api/server-snapshots/${snapshotId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showMessage('成功', data.message);
            refreshData();
        } else {
            showMessage('错误', data.error || '删除云主机快照失败');
        }
    })
    .catch(error => {
        hideLoading();
        showMessage('错误', '删除云主机快照失败: ' + error.message);
    });
}

// 删除云硬盘快照
function deleteVolumeSnapshot(snapshotId) {
    if (!confirm('确定要删除这个云硬盘快照吗？此操作不可恢复。')) {
        return;
    }
    
    showLoading();
    
    fetch(`/api/volume-snapshots/${snapshotId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showMessage('成功', data.message);
            refreshData();
        } else {
            showMessage('错误', data.error || '删除云硬盘快照失败');
        }
    })
    .catch(error => {
        hideLoading();
        showMessage('错误', '删除云硬盘快照失败: ' + error.message);
    });
}

// 清理快照
function cleanupSnapshots() {
    const cleanupType = document.querySelector('input[name="snapshotCleanupType"]:checked').value;
    const retentionDays = parseInt(document.getElementById('snapshotRetentionDays').value);
    
    if (!retentionDays || retentionDays < 1 || retentionDays > 365) {
        showMessage('错误', '请输入有效的保留天数（1-365天）');
        return;
    }
    
    if (!confirm(`确定要清理超过 ${retentionDays} 天的${cleanupType === 'server' ? '云主机' : '云硬盘'}快照吗？此操作不可恢复。`)) {
        return;
    }
    
    showLoading();
    
    const endpoint = cleanupType === 'server' ? '/api/server-snapshots/cleanup' : '/api/volume-snapshots/cleanup';
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            retention_days: retentionDays
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showMessage('成功', data.message);
            bootstrap.Modal.getInstance(document.getElementById('snapshotCleanupModal')).hide();
            refreshData();
        } else {
            showMessage('错误', data.error || '清理快照失败');
        }
    })
    .catch(error => {
        hideLoading();
        showMessage('错误', '清理快照失败: ' + error.message);
    });
} 