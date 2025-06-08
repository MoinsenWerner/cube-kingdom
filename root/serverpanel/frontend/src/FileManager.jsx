import React, { useState, useEffect } from 'react';
import axios from 'axios';

function FileManager({ apiKey, server }) {
  const [files, setFiles] = useState([]);
  const [path, setPath] = useState('');
  const [selected, setSelected] = useState([]);
  const [newFolderName, setNewFolderName] = useState('');
  const [uploading, setUploading] = useState(false);

  const authHeader = { headers: { 'x-api-key': apiKey } };

  const fetchFiles = async () => {
    try {
      const res = await axios.get('/files/list', {
        ...authHeader,
        params: { server, path }
      });

      const sorted = [...res.data.items].sort((a, b) => {
        if (a.type !== b.type) return a.type === 'dir' ? -1 : 1;
        return a.name.localeCompare(b.name);
      });

      setFiles(sorted);
    } catch (err) {
      console.error('Fehler beim Laden der Dateien:', err);
    }
  };

  useEffect(() => {
    if (server) {
      fetchFiles();
    }
  }, [server, path]);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append('server', server);
    form.append('path', path);
    form.append('file', file);
    setUploading(true);
    try {
      await axios.post('/files/upload', form, authHeader);
      fetchFiles();
    } catch {
      alert('❌ Upload fehlgeschlagen');
    }
    setUploading(false);
  };

  const handleDelete = async () => {
    if (selected.length === 0) return;
    try {
      await axios.post('/files/delete', {
        server,
        paths: selected
      }, authHeader);
      setSelected([]);
      fetchFiles();
    } catch {
      alert('❌ Löschen fehlgeschlagen');
    }
  };

  const handleMkdir = async () => {
    if (!newFolderName) return;
    const form = new FormData();
    form.append('server', server);
    form.append('path', path);
    form.append('name', newFolderName);
    try {
      await axios.post('/files/mkdir', form, authHeader);
      setNewFolderName('');
      fetchFiles();
    } catch {
      alert('❌ Ordner konnte nicht erstellt werden');
    }
  };

  const toggleSelect = (name) => {
    setSelected((prev) =>
      prev.includes(name)
        ? prev.filter((n) => n !== name)
        : [...prev, name]
    );
  };

  const enterFolder = (folderName) => {
    setPath(path ? `${path}/${folderName}` : folderName);
    setSelected([]);
  };

  const goUp = () => {
    const parts = path.split('/').filter(Boolean);
    parts.pop();
    setPath(parts.join('/'));
    setSelected([]);
  };

  const downloadFile = (name) => {
    const fullPath = path ? `${path}/${name}` : name;
    const url = `/api/files/download?server=${server}&path=${encodeURIComponent(fullPath)}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="text-xl font-semibold mb-4">📁 Dateimanager: {server} ({path || '/'})</h2>
      <div className="flex gap-2 mb-4 flex-wrap">
        <input type="file" onChange={handleUpload} disabled={uploading} />
        <button onClick={goUp} className="bg-gray-300 px-2 py-1 rounded" title="Eine Ebene hoch">⬆️ Ordner hoch</button>
        <input
          placeholder="Neuer Ordnername"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          className="border px-2 py-1"
        />
        <button onClick={handleMkdir} className="bg-green-500 text-white px-3 py-1 rounded">📂 Erstellen</button>
        {selected.length > 0 && (
          <button onClick={handleDelete} className="bg-red-500 text-white px-3 py-1 rounded">
            🗑️ Löschen ({selected.length})
          </button>
        )}
      </div>
      <ul className="text-sm">
        {files.map(file => (
          <li
            key={file.name}
            className={`cursor-pointer px-2 py-1 rounded ${selected.includes(file.name) ? 'selected' : ''}`}
            onClick={() =>
              file.type === 'dir'
                ? enterFolder(file.name)
                : downloadFile(file.name)
            }
            onContextMenu={(e) => {
              e.preventDefault();
              toggleSelect(file.name);
            }}
          >
            {file.type === 'dir' ? '📁' : '📄'} {file.name}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default FileManager;
