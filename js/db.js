let _db = null;
let _promise = null;

export async function getDB() {
  if (_db) return _db;
  if (_promise) return _promise;

  _promise = (async () => {
    try {
      const SQL = await window.initSqlJs({
        locateFile: file =>
          `https://cdn.jsdelivr.net/npm/sql.js@1.10.3/dist/${file}`
      });

      const res = await fetch("data/pynumstore.db");
      if (!res.ok) throw new Error(`Failed to fetch DB : ${res.status}`);

      const buffer = await res.arrayBuffer();
      _db = new SQL.Database(new Uint8Array(buffer));
      return _db;
    } catch (err) {
      _promise = null;
      throw err;
    }
  })();

  return _promise;
}

export function queryAll(db, sql, params = []) {
  const stmt = db.prepare(sql);
  stmt.bind(params);
  const rows = [];
  while (stmt.step()) rows.push(stmt.getAsObject());
  stmt.free();
  return rows;
}

export function queryOne(db, sql, params = []) {
  const rows = queryAll(db, sql, params);
  return rows[0] ?? null;
}