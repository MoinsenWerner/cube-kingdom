import React, { useEffect, useState } from 'react';
import axios from 'axios';

function AdminPanel({ apiKey }) {
  const [licenses, setLicenses] = useState([]);
  const [newKey, setNewKey] = useState('');
  const [newDate, setNewDate] = useState('');
  const [error, setError] = useState(null);

  const fetchLicenses = async () => {
    try {
      const res = await axios.get('/licenses', {
        headers: { 'x-api-key': apiKey }
      });
      setLicenses(res.data);
    } catch (e) {
      setError('❌ Fehler beim Laden der Lizenzen');
    }
  };

  const updateLicense = async (key, active, valid_until) => {
    await axios.post('/licenses/update', {
      key, active, valid_until
    }, {
      headers: { 'x-api-key': apiKey }
    });
    fetchLicenses();
  };

  const deleteLicense = async (key) => {
    await axios.post('/licenses/delete', { key }, {
      headers: { 'x-api-key': apiKey }
    });
    fetchLicenses();
  };

  const createLicense = async () => {
    await axios.post('/licenses/add', {
      key: newKey || undefined,
      valid_until: newDate || null,
      active: 1,
      admin: 0
    }, {
      headers: { 'x-api-key': apiKey }
    });
    setNewKey('');
    setNewDate('');
    fetchLicenses();
  };

// eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    fetchLicenses();
  }, []);

  return (
    <div className="bg-white p-4 rounded shadow mt-6">
      <h2 className="text-xl font-bold mb-4">🔐 Adminpanel: Lizenzverwaltung</h2>

      {error && <p className="text-red-600">{error}</p>}

      <table className="w-full text-sm mb-4">
        <thead>
          <tr className="bg-gray-100">
            <th className="text-left px-2 py-1">Key</th>
            <th className="text-left px-2 py-1">Gültig bis</th>
            <th className="text-left px-2 py-1">Aktiv</th>
            <th className="text-left px-2 py-1">Admin</th>
            <th className="text-left px-2 py-1">Aktionen</th>
          </tr>
        </thead>
        <tbody>
          {licenses.map((lic) => (
            <tr key={lic.key} className="border-t">
              <td className="px-2 py-1 break-all">{lic.key}</td>
              <td className="px-2 py-1">{lic.valid_until || '—'}</td>
              <td className="px-2 py-1">{lic.active ? '✅' : '❌'}</td>
              <td className="px-2 py-1">{lic.admin ? '🛡️' : ''}</td>
              <td className="px-2 py-1 space-x-2">
                <button
                  onClick={() => updateLicense(lic.key, lic.active ? 0 : 1, lic.valid_until)}
                  className="text-blue-500 underline"
                >
                  {lic.active ? 'deaktivieren' : 'aktivieren'}
                </button>
                <button
                  onClick={() => updateLicense(lic.key, lic.active, null)}
                  className="text-yellow-600 underline"
                >
                  Laufzeit entfernen
                </button>
                <button
                  onClick={() => deleteLicense(lic.key)}
                  className="text-red-600 underline"
                >
                  löschen
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-4">
        <h3 className="font-semibold mb-2">➕ Neuen Key erstellen</h3>
        <div className="flex flex-col md:flex-row gap-2">
          <input
            type="text"
            placeholder="optional benutzerdefiniert"
            className="border px-2 py-1 flex-1"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
          />
          <input
            type="date"
            className="border px-2 py-1"
            value={newDate}
            onChange={(e) => setNewDate(e.target.value)}
          />
          <button
            onClick={createLicense}
            className="bg-green-600 text-white px-3 py-1 rounded"
          >
            speichern
          </button>
        </div>
      </div>
    </div>
  );
}

export default AdminPanel;
