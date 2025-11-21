/**
 * Run:
 *   node upload_to_firestore.js
 */

const admin = require("firebase-admin");
const fs = require("fs");
const readline = require("readline");

admin.initializeApp({
  credential: admin.credential.cert("./byte.json"),   // your service account
});

const db = admin.firestore();
const bulkWriter = db.bulkWriter();

// automatic retry on transient failures
bulkWriter.onWriteError((err) => {
  console.log("Retrying write:", err.documentRef.path);
  return true; // retry
});

async function main() {
  const fileStream = fs.createReadStream("./tracks_prepared.jsonl");
  const rl = readline.createInterface({ input: fileStream });

  let count = 0;

  for await (const line of rl) {
    if (!line.trim()) continue;

    const data = JSON.parse(line);
    const id = data.track_id;

    bulkWriter.set(db.collection("tracks").doc(id), data);
    count++;

    if (count % 5000 === 0) {
      console.log(`Queued ${count} docs...`);
    }
  }

  console.log("Finishing Firestore writes...");
  await bulkWriter.close();
  console.log(`DONE: Uploaded ${count} tracks.`);
}

main().catch(console.error);
