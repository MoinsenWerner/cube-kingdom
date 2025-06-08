import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './output.css';
import AdminPanel from './AdminPanel';
import FileManager from './FileManager';

axios.defaults.baseURL = '/api';

const setLicenseKey = (key) => localStorage.setItem('licenseKey', key);
const getLicenseKey = () => localStorage.getItem('licenseKey');
const clearLicenseKey = () => localStorage.removeItem('licenseKey');

function App() {
  const [apiKey, setApiKey] = useState('');
  const [authenticated, setAuthenticated] = useState(false);
  const [serverList, setServerList] = useState([]);
  const [selectedServer, setSelectedServer] = useState('');
  const [serverStatus, setServerStatus] = useState(null);
  const [logs, setLogs] = useState('');
  const [busy, setBusy] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminMode, setAdminMode] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [licenseType, setLicenseType] = useState('basic');
  const [fileManagerMode, setFileManagerMode] = useState(false);

  const authHeader = () => ({ headers: { 'x-api-key': apiKey } });

  const fetchServerList = async (keyOverride = null) => {
    const keyToUse = keyOverride || apiKey;
    const res = await axios.get('/servers', {
      headers: { 'x-api-key': keyToUse }
    });
    setServerList(res.data);
    if (res.data.length > 0) {
      setSelectedServer(res.data[0]);
    }
  };

  const fetchStatus = async () => {
    if (!selectedServer) return;
    try {
      const res = await axios.get(`/status?name=${selectedServer}`, authHeader());
      setServerStatus(res.data[`minecraft@${selectedServer}`]);
      setErrorMessage(null);
    } catch {
      setServerStatus(null);
      setErrorMessage('❌ Fehler beim Abrufen des Serverstatus.');
    }
  };

  const fetchLogs = async () => {
    if (!selectedServer) return;
    try {
      const res = await axios.get('/logs', {
        ...authHeader(),
        params: { service: `minecraft@${selectedServer}` }
      });
      setLogs(res.data.log);
    } catch {
      setLogs('❌ Fehler beim Laden der Logs');
    }
  };

  const control = async (action) => {
    if (!selectedServer || busy) return;
    setBusy(true);
    try {
      await axios.post('/control', {
        action,
        service: `minecraft@${selectedServer}`
      }, authHeader());
      setTimeout(fetchStatus, 500);
    } catch {
      setErrorMessage(`❌ Fehler beim ${action}`);
    }
    setTimeout(() => setBusy(false), 1250);
  };

  useEffect(() => {
    const savedKey = getLicenseKey();
    if (savedKey) {
      setApiKey(savedKey);
      axios
        .get('/me', {
          headers: { 'x-api-key': savedKey }
        })
        .then(async (meRes) => {
          setIsAdmin(meRes.data.admin === 1);
          setLicenseType(meRes.data.license_type || 'basic');
          setAuthenticated(true);
          await fetchServerList(savedKey);
        })
        .catch((err) => {
          console.warn("⚠️ Auto-Login fehlgeschlagen", err?.response?.status);
          if (err.response?.status === 403) {
            clearLicenseKey(); // nur löschen, wenn tatsächlich ungültig
          }
          setAuthenticated(false);
          setApiKey('');
        });
    }
  }, []);

  useEffect(() => {
    if (!authenticated || !selectedServer) return;

    fetchStatus();
    fetchLogs();

    const intervalId = setInterval(() => {
      fetchStatus();
      fetchLogs();
    }, 1300); // oder dein gewünschter Wert in ms

    return () => {
      clearInterval(intervalId); // ← Wichtig: vorherigen abbrechen
    };
  }, [selectedServer, authenticated]);

  const handleLogin = async () => {
    try {
      await axios.get('/status', { headers: { 'x-api-key': apiKey } });
      const me = await axios.get('/me', { headers: { 'x-api-key': apiKey } });
      setIsAdmin(me.data.admin === 1);
      setLicenseType(me.data.license_type || 'basic');
      setAuthenticated(true);
      setLicenseKey(apiKey);
      await fetchServerList();
    } catch {
      setErrorMessage('❌ Login fehlgeschlagen.');
    }
  };

  const handleLogout = () => {
    clearLicenseKey();
    setApiKey('');
    setAuthenticated(false);
    setSelectedServer('');
    setServerList([]);
    setServerStatus(null);
    setLogs('');
    setErrorMessage(null);
  };

  if (!authenticated) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="bg-white p-6 rounded shadow-md w-96">
          <h1 className="text-2xl font-semibold mb-4">Server Login</h1>
          <input
            className="border px-4 py-2 w-full mb-3"
            placeholder="API Key eingeben"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <button
            onClick={handleLogin}
            className="bg-blue-500 text-white px-4 py-2 w-full rounded"
          >
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="flex justify-between mb-4">
        <h1 className="text-3xl font-bold">Serverübersicht</h1>
        <div className="flex gap-2">
          {!adminMode && (
            <button
              onClick={() => setFileManagerMode(!fileManagerMode)}
              className="bg-indigo-500 text-white px-3 py-1 rounded shadow hover:bg-indigo-600"
            >
              🗂️ Dateien
            </button>
          )}
          {isAdmin && (
            <button
              onClick={() => setAdminMode(!adminMode)}
              className="bg-purple-600 text-white px-3 py-1 rounded shadow hover:bg-purple-800"
            >
              🛡️ Admin
            </button>
          )}
          <button
            onClick={fetchStatus}
            className="bg-blue-500 text-white px-3 py-1 rounded shadow"
          >
            🔄 Neu laden
          </button>
          <button
            onClick={handleLogout}
            className="bg-gray-400 text-white px-3 py-1 rounded shadow"
          >
            🚪 Logout
          </button>
        </div>
      </div>

      {serverList.length > 0 && (
        <div className="mb-4">
          <label className="mr-2 font-semibold">Server auswählen:</label>
          <select
            className="border px-2 py-1"
            value={selectedServer}
            onChange={(e) => setSelectedServer(e.target.value)}
          >
            {serverList.map((srv) => (
              <option key={srv} value={srv}>{srv}</option>
            ))}
          </select>
        </div>
      )}

      {errorMessage && (
        <div className="bg-red-100 text-red-800 p-2 mb-4 rounded shadow">{errorMessage}</div>
      )}

      {serverStatus && (
        <div className="bg-white rounded shadow p-4 mb-4">
          <h2 className="text-xl font-semibold mb-2">minecraft@{selectedServer}</h2>
          <p className="font-semibold">
            {serverStatus.status === 'online' && (
              <span className="text-green-600">🟢 Status: online</span>
            )}
            {serverStatus.status === 'active_unresponsive' && (
              <span className="text-orange-500">🟠 Status: startet...</span>
            )}
            {serverStatus.status === 'inactive' && (
              <span className="text-red-600">🔴 Status: offline</span>
            )}
          </p>
          <p>RAM: {serverStatus.memory ?? '?'} MB</p>
          <p>CPU: {serverStatus.cpu ?? '?'}%</p>
            {(licenseType === 'pro' || licenseType === 'super' || isAdmin) && (
              <p>👥 Spieler online: {serverStatus.player_count ?? '?'}</p>
            )}

            {(licenseType === 'super' || isAdmin) && (
              <div className="mt-3 flex gap-2 flex-wrap">
                <button
                  className="bg-blue-600 text-white px-3 py-1 rounded"
                  disabled
                >
                  📦 Backup erstellen
                </button>
                <button
                  className="bg-indigo-600 text-white px-3 py-1 rounded"
                  disabled
                >
                  ♻️ Backup wiederherstellen
                </button>
              </div>
            )}
          <div className="mt-3 flex gap-2 flex-wrap">
            <button
              className="bg-green-500 text-white px-3 py-1 rounded"
              onClick={() => control('start')}
              disabled={busy}
            >
              Start
            </button>
            <button
              className="bg-yellow-500 text-white px-3 py-1 rounded"
              onClick={() => control('restart')}
              disabled={busy}
            >
              Restart
            </button>
            <button
              className="bg-red-500 text-white px-3 py-1 rounded"
              onClick={() => control('stop')}
              disabled={busy}
            >
              Stop
            </button>
          </div>
        </div>
      )}

      {fileManagerMode ? (
        <FileManager apiKey={apiKey} server={selectedServer} />
      ) : (
        logs && (
          <div className="bg-white p-4 rounded shadow mt-6">
            <h3 className="text-lg font-bold mb-2">Logs: minecraft@{selectedServer}</h3>
            <pre className="text-sm overflow-auto max-h-96 bg-gray-100 p-2 rounded whitespace-pre-wrap">{logs}</pre>
          </div>
        )
      )}
      {adminMode && <AdminPanel apiKey={apiKey} />}
    </div>
  );
}

export default App;
