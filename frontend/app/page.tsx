"use client";

import { useRef, useState } from "react";

const API =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Reel = {
  id: number;
  filename: string;
  status: string;
  duration?: string;
  transcript: string;
  analysis: any;
  optimized_url?: string | null;
};

type ChatMessage = {
  role: "ai" | "user";
  text: string;
};

export default function Home() {
  const input = useRef<HTMLInputElement>(null);

  const [reel, setReel] = useState<Reel | null>(null);
  const [uploading, setUploading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [chatBusy, setChatBusy] = useState(false);
  const [error, setError] = useState("");

  const [chat, setChat] = useState<ChatMessage[]>([
    {
      role: "ai",
      text: "Upload a Reel and I’ll analyze the hook, pacing, CTA and optimization opportunities.",
    },
  ]);

  const [message, setMessage] = useState("");

  // ------------------------------------------------------------
  // UPLOAD
  // ------------------------------------------------------------

  async function upload(file: File) {
    setUploading(true);
    setError("");

    try {
      const fd = new FormData();
      fd.append("file", file);

      const response = await fetch(
        `${API}/api/reels/upload`,
        {
          method: "POST",
          body: fd,
        }
      );

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Upload failed");
      }

      const data: Reel = await response.json();

      setReel(data);

      setChat([
        {
          role: "ai",
          text: `"${data.filename}" uploaded successfully. I'm analyzing your Reel now.`,
        },
      ]);

      await analyze(data.id);
    } catch (err: any) {
      setError(err?.message || "Something went wrong while uploading.");
    } finally {
      setUploading(false);
    }
  }

  // ------------------------------------------------------------
  // ANALYZE
  // ------------------------------------------------------------

  async function analyze(id: number) {
    setBusy(true);
    setError("");

    try {
      const response = await fetch(
        `${API}/api/reels/${id}/analyze`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Analysis failed");
      }

      const data: Reel = await response.json();

      setReel(data);

      if (data.analysis) {
        const score =
          data.analysis.viral_score ??
          data.analysis.viralPotential ??
          "—";

        const issues =
          data.analysis.issues || [];

        setChat((current) => [
          ...current,
          {
            role: "ai",
            text: `Analysis complete. Viral potential: ${score}/100. I found ${issues.length} issue${issues.length === 1 ? "" : "s"}.`,
          },
        ]);
      }
    } catch (err: any) {
      setError(err?.message || "Reel analysis failed.");

      setChat((current) => [
        ...current,
        {
          role: "ai",
          text: "I couldn't complete the Reel analysis. Please check the backend logs and try again.",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  // ------------------------------------------------------------
  // CHAT
  // ------------------------------------------------------------

  async function send() {
    if (!reel || !message.trim() || chatBusy) {
      return;
    }

    const text = message.trim();

    setMessage("");

    setChat((current) => [
      ...current,
      {
        role: "user",
        text,
      },
    ]);

    setChatBusy(true);
    setError("");

    try {
      const response = await fetch(
        `${API}/api/reels/${reel.id}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: text,
          }),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          errorText || "Chat request failed"
        );
      }

      const data = await response.json();

      setChat((current) => [
        ...current,
        {
          role: "ai",
          text:
            data.message ||
            "I couldn't generate a response.",
        },
      ]);
    } catch (err: any) {
      setChat((current) => [
        ...current,
        {
          role: "ai",
          text:
            "Sorry, I couldn't process that request right now.",
        },
      ]);

      setError(err?.message || "Chat request failed.");
    } finally {
      setChatBusy(false);
    }
  }

  // ------------------------------------------------------------
  // OPTIMIZE
  // ------------------------------------------------------------

  async function optimize() {
    if (!reel || busy) {
      return;
    }

    const confirmed = confirm(
      "Create an optimized preview? Your original Reel will remain unchanged."
    );

    if (!confirmed) {
      return;
    }

    setBusy(true);
    setError("");

    try {
      const response = await fetch(
        `${API}/api/reels/${reel.id}/optimize`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            actions: ["safe_auto_optimize"],
          }),
        }
      );

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Optimization failed");
      }

      const data: Reel = await response.json();

      setReel(data);

      if (data.optimized_url) {
        setChat((current) => [
          ...current,
          {
            role: "ai",
            text: "Optimized preview is ready. Your original Reel was not modified.",
          },
        ]);
      }
    } catch (err: any) {
      setError(
        err?.message || "Failed to create optimized Reel."
      );
    } finally {
      setBusy(false);
    }
  }

  // ------------------------------------------------------------
  // DATA
  // ------------------------------------------------------------

  const analysis = reel?.analysis || {};

  const scores =
    analysis.scores || {};

  const issues =
    analysis.issues || [];

  const recommendations =
    analysis.recommendations || [];

  // ------------------------------------------------------------
  // UI
  // ------------------------------------------------------------

  return (
    <main>
      <header className="top">
        <div className="brand">
          <span className="dot" />
          ReelMind
        </div>

        <div className="pill">
          AI Creator OS
        </div>
      </header>

      {/* HERO */}

      <section className="hero">
        <div>
          <div className="eyebrow">
            CREATE • ANALYZE • OPTIMIZE
          </div>

          <h1>
            Make every Reel
            <br />
            <em>worth watching.</em>
          </h1>

          <p>
            Upload a Reel, chat with your AI growth
            agent, find weak points and generate an
            optimized version.
          </p>

          <button
            className="primary"
            onClick={() => input.current?.click()}
            disabled={uploading}
          >
            {uploading
              ? "Uploading…"
              : "Upload Reel"}
          </button>

          <input
            ref={input}
            hidden
            type="file"
            accept="video/mp4,video/quicktime,video/webm,video/x-m4v"
            onChange={(event) => {
              const file =
                event.target.files?.[0];

              if (file) {
                upload(file);
              }

              event.target.value = "";
            }}
          />
        </div>

        {/* SCORE */}

        <div className="scoreCard">
          <div className="mini">
            VIRAL POTENTIAL
          </div>

          <div className="score">
            {analysis.viral_score ?? "—"}
            <small>/100</small>
          </div>

          <div className="bars">
            {Object.entries(scores).map(
              ([key, value]: any) => (
                <div
                  className="bar"
                  key={key}
                >
                  <span>
                    {key}
                  </span>

                  <div>
                    <i
                      style={{
                        width: `${Math.min(
                          100,
                          Math.max(
                            0,
                            Number(value) || 0
                          )
                        )}%`,
                      }}
                    />
                  </div>

                  <b>
                    {value}
                  </b>
                </div>
              )
            )}
          </div>
        </div>
      </section>

      {/* ERROR */}

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {/* WORKSPACE */}

      <section className="workspace">
        {/* ------------------------------------------------ */}
        {/* ORIGINAL PREVIEW */}
        {/* ------------------------------------------------ */}

        <div className="panel preview">
          <div className="panelHead">
            <b>
              REEL PREVIEW
            </b>

            <span>
              {reel?.status ||
                "Waiting for upload"}
            </span>
          </div>

          {!reel ? (
            <div
              className="drop"
              onClick={() =>
                input.current?.click()
              }
            >
              <strong>
                Drop your Reel here
              </strong>

              <span>
                MP4, MOV, WEBM · up to 200 MB
              </span>
            </div>
          ) : (
            <>
              <video
                className="video"
                src={`${API}/api/reels/${reel.id}/preview`}
                controls
                playsInline
                preload="metadata"
              />

              <div className="videoName">
                {reel.filename}
              </div>
            </>
          )}

          {reel && (
            <button
              className="secondary"
              disabled={busy}
              onClick={optimize}
            >
              {busy
                ? "Working…"
                : "✨ Fix recommended issues"}
            </button>
          )}

          {reel?.optimized_url && (
            <div className="optimizedPreview">
              <div className="optimizedTitle">
                OPTIMIZED REEL
              </div>

              <video
                className="video"
                src={`${API}${reel.optimized_url}`}
                controls
                playsInline
                preload="metadata"
              />

              <a
                className="download"
                href={`${API}${reel.optimized_url}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open optimized Reel
              </a>
            </div>
          )}
        </div>

        {/* ------------------------------------------------ */}
        {/* AI DIAGNOSIS */}
        {/* ------------------------------------------------ */}

        <div className="panel analysis">
          <div className="panelHead">
            <b>
              AI DIAGNOSIS
            </b>

            <span>
              {reel?.duration
                ? `${reel.duration}s`
                : "—"}
            </span>
          </div>

          {!reel ? (
            <div className="empty">
              Your analysis will appear here.
            </div>
          ) : (
            <>
              {issues.length === 0 &&
                !busy && (
                  <div className="empty">
                    No issues detected yet.
                  </div>
                )}

              {issues.map(
                (
                  issue: any,
                  index: number
                ) => (
                  <div
                    className="issue"
                    key={index}
                  >
                    <div
                      className={`severity ${
                        issue.severity ||
                        "medium"
                      }`}
                    />

                    <div>
                      <b>
                        {issue.type ||
                          "Issue"}
                      </b>

                      <p>
                        {issue.message ||
                          "Potential optimization opportunity detected."}
                      </p>
                    </div>
                  </div>
                )
              )}

              {recommendations.length >
                0 && (
                <>
                  <h3>
                    Recommended actions
                  </h3>

                  {recommendations.map(
                    (
                      recommendation: string,
                      index: number
                    ) => (
                      <div
                        className="rec"
                        key={index}
                      >
                        ✓{" "}
                        {recommendation}
                      </div>
                    )
                  )}
                </>
              )}
            </>
          )}
        </div>

        {/* ------------------------------------------------ */}
        {/* AI CHATBOT */}
        {/* ------------------------------------------------ */}

        <div className="panel chat">
          <div className="panelHead">
            <b>
              AI GROWTH AGENT
            </b>

            <span>
              ● online
            </span>
          </div>

          <div className="messages">
            {chat.map(
              (item, index) => (
                <div
                  className={`msg ${item.role}`}
                  key={index}
                >
                  <span>
                    {item.role === "ai"
                      ? "RM"
                      : "YOU"}
                  </span>

                  <p>
                    {item.text}
                  </p>
                </div>
              )
            )}

            {chatBusy && (
              <div className="msg ai">
                <span>RM</span>
                <p>
                  Thinking…
                </p>
              </div>
            )}
          </div>

          <div className="composer">
            <input
              value={message}
              onChange={(event) =>
                setMessage(
                  event.target.value
                )
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter"
                ) {
                  send();
                }
              }}
              placeholder="Ask: improve my hook…"
              disabled={
                !reel || chatBusy
              }
            />

            <button
              onClick={send}
              disabled={
                !reel ||
                chatBusy ||
                !message.trim()
              }
            >
              ↑
            </button>
          </div>
        </div>
      </section>

      <footer>
        ReelMind By Dazzle · Optimization
        scores are estimates, not guarantees
        of virality.
      </footer>
    </main>
  );
}