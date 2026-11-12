# OnlineBookArchiver

## WSL 访问 Windows 浏览器 CDP

归档程序会连接一个已经存在的 Chrome/Edge CDP 地址。浏览器运行在 Windows 宿主机上，WSL 通过 Windows 的 CDP 端口访问浏览器。

### 配置 Windows 端口转发和防火墙规则

用管理员权限打开 Windows PowerShell，执行：

```powershell
netsh interface portproxy add v4tov4 listenaddress=172.16.103.78 listenport=9224 connectaddress=127.0.0.1 connectport=9224
netsh interface portproxy add v4tov4 listenaddress=172.16.103.78 listenport=9225 connectaddress=127.0.0.1 connectport=9225

New-NetFirewallRule -DisplayName "Chrome CDP 9224 for WSL" -Direction Inbound -Action Allow -Protocol TCP -LocalAddress 172.16.103.78 -LocalPort 9224
New-NetFirewallRule -DisplayName "Edge CDP 9225 for WSL" -Direction Inbound -Action Allow -Protocol TCP -LocalAddress 172.16.103.78 -LocalPort 9225
```

### 启动浏览器 CDP

在 Windows PowerShell 中启动 Edge：

```powershell
.\scripts\Start-BrowserCdp.ps1 `
  -Browser edge `
  -Port 9225 `
  -WslHostAddress 172.16.103.78
```

如果遇到 PowerShell 执行策略限制，使用：

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\Start-BrowserCdp.ps1" -Browser edge -Port 9225 -WslHostAddress 172.16.103.78
```

启动 Chrome：

```powershell
.\scripts\Start-BrowserCdp.ps1 `
  -Browser chrome `
  -Port 9224 `
  -WslHostAddress 172.16.103.78
```

如果遇到 PowerShell 执行策略限制，使用：

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\Start-BrowserCdp.ps1" -Browser chrome -Port 9224 -WslHostAddress 172.16.103.78
```

### 检查 Edge CDP 端口转发

启动 Edge CDP 后，用管理员权限打开 Windows PowerShell。先重启 IP Helper 服务，使已保存的 `portproxy` 规则重新加载：

```powershell
Restart-Service iphlpsvc
```

然后检查 9225 端口的实际监听状态：

```powershell
Get-NetTCPConnection -State Listen -LocalPort 9225 |
  Select-Object LocalAddress, LocalPort, OwningProcess
```

正常情况下，结果中应同时包含 Edge 的本地监听地址 `127.0.0.1:9225` 和端口转发监听地址 `172.16.103.78:9225`。如果只有 `127.0.0.1:9225`，说明 `portproxy` 规则虽然可能已经保存，但尚未形成实际监听。

脚本会复制当前浏览器 profile 到临时目录，然后用临时 profile 启动浏览器并开启 remote debugging。启动完成后，脚本会输出：

- Windows 本地 CDP URL
- WSL 可访问的 CDP URL
- 停止浏览器进程的命令
- 删除临时 profile 的命令

在 WSL 中运行 live browser 测试或归档命令时，使用脚本输出的 WSL CDP URL。例如：

`http://172.16.103.78:9225`
