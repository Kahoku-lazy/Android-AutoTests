.panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  
  border-radius: 6px 10px 6px 10px;
  border: 3px solid var(--app-ink, #2d2d2d);
  padding: 16px;
  box-shadow: 2px 3px 0 rgba(0,0,0,0.05);
  overflow-y: auto;
.panel::before {
  content: '';
  position: absolute; top: 4px; left: 50%; transform: translateX(-50%);
  width: 9px; height: 9px;
  background: radial-gradient(circle, #e8e0d5 30%, #c0b8a8 60%, #a09080 100%);
  border-radius: 50%;
  box-shadow: 0 1px 1px rgba(0,0,0,0.08);
  z-index: 10;
}
}
h3 {
  font-size: 14px;
  color: var(--app-text, var(--app-ink));
  margin-bottom: 12px;
  flex-shrink: 0;
}
.meta {
  font-size: 12px;
  line-height: 1.6;
}
.meta p {
  margin-bottom: 6px;
  color: var(--app-text-secondary, var(--app-ink-muted));
  word-break: break-all;
}
.meta strong {
  color: var(--app-text, var(--app-ink));
}
.placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 200px;
}
.placeholder-icon {
  font-size: 32px;
  opacity: 0.5;
}
.placeholder-label {
  font-size: 15px;
  font-weight: 500;
  color: var(--app-ink);
}
.hint {
  margin: 0;
  font-size: 12px;
  color: var(--app-text-secondary, var(--app-ink-muted));
  opacity: 0.5;
}
</style>
