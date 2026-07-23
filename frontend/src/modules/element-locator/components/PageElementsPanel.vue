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
  position: relative; overflow: hidden; padding-top: 6px;
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
.pe-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-shrink: 0;
}
.pe-header h3 {
  font-size: 14px;
  color: var(--app-text, var(--app-ink));
  margin: 0;
}
.pe-count {
  font-size: 12px;
  color: var(--app-text-secondary, var(--app-ink-muted));
  background: rgba(179, 158, 243,0.06);
  padding: 1px 8px;
  border-radius: 6px 10px 6px 10px;
}

/* Toolbar */
.pe-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  flex-shrink: 0;
  padding: 6px 10px;
  background: rgba(179, 158, 243,0.04);
  border-radius: 4px 8px 4px 8px;
}
.pe-refresh-btn {
  padding: 4px 10px;
  font-size: 12px;
  border: 3px solid var(--app-ink, #2d2d2d);
  border-radius: 4px 8px 4px 8px;
  background: #fff;
  color: var(--app-text, var(--app-ink));
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.pe-refresh-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.pe-refresh-btn:not(:disabled):hover {
  border-color: var(--app-purple, #b39ef3);
  color: var(--app-purple, #b39ef3);
}
.pe-check-all {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--app-text, var(--app-ink));
  cursor: pointer;
  user-select: none;
}
.pe-checked-count {
  font-size: 12px;
  color: var(--app-text-secondary, var(--app-ink-muted));
}
.pe-batch-btn {
  margin-left: auto;
  padding: 4px 12px;
  font-size: 12px;
  border: 3px solid var(--app-ink, #2d2d2d);
  border-radius: 4px 8px 4px 8px;
  background: #fff;
  color: var(--app-text, var(--app-ink));
  cursor: pointer;
  transition: all 0.2s;
}
.pe-batch-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.pe-batch-btn:not(:disabled):hover {
  border-color: var(--app-teal, var(--app-accent-purple));
  color: var(--app-teal, var(--app-accent-purple));
}

/* Empty */
.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--app-text-secondary, var(--app-ink-muted));
  font-size: 13px;
}
.empty-icon { font-size: 32px; opacity: 0.55; }
.empty-text { margin: 0; font-size: 13px; font-weight: 500; color: var(--app-text, var(--app-text)); }

/* Element list */
.pe-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}
.pe-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 6px;
  border-radius: 4px 8px 4px 8px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
}
.pe-row:hover {
  background: rgba(179, 158, 243,0.04);
}
.pe-row--selected {
  background: rgba(179, 158, 243,0.08);
  border-color: var(--app-teal, var(--app-accent-purple));
}
.pe-row--checked {
  background: rgba(179, 158, 243,0.04);
}

.pe-checkbox {
  flex-shrink: 0;
  cursor: pointer;
  accent-color: var(--app-teal, var(--app-accent-purple));
}

/* Cells */
.pe-cell {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  min-width: 0;
}
.pe-cell--thumb {
  width: 56px;
  justify-content: center;
}
.pe-thumb {
  border-radius: 4px;
  border: 3px solid var(--app-ink, #2d2d2d);
  background-repeat: no-repeat;
  flex-shrink: 0;
  cursor: zoom-in;
  transition: transform 0.15s;
}
.pe-thumb:hover {
  transform: scale(1.1);
  border-color: var(--app-teal, var(--app-accent-purple));
  z-index: 1;
}
.pe-thumb-placeholder {
  font-size: 18px;
  opacity: 0.4;
  width: 36px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pe-cell--text {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pe-text { color: var(--app-text, var(--app-ink)); }
.pe-text--desc { color: var(--app-text-secondary, var(--app-ink-muted)); font-style: italic; }
.pe-text--none { color: var(--app-ink-muted); }
.pe-cell--bounds {
  width: 110px;
  font-size: 11px;
  overflow: hidden;
}
.pe-code {
  font-size: 10px;
  color: var(--app-text-secondary, var(--app-ink-muted));
  background: rgba(179, 158, 243,0.04);
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.pe-cell--clickable {
  width: 32px;
  justify-content: center;
}
.pe-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
}
.pe-badge--yes {
  color: var(--app-accent-purple);
  background: rgba(179, 158, 243,0.1);
}
.pe-badge--no {
  color: var(--app-ink-muted);
}

/* Form */
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form-label {
  font-size: 13px;
  color: var(--text-secondary, var(--app-ink-muted));
  font-weight: 500;
  user-select: none;
}
.form-label.required::before {
  content: '* ';
  color: var(--el-color-danger, #FFB5A7);
}
.form-hint {
  font-size: 12px;
  color: var(--app-text-secondary, var(--app-ink-muted));
  line-height: 1.5;
  background: rgba(179, 158, 243,0.04);
  padding: 8px 10px;
  border-radius: 4px 8px 4px 8px;
}

/* Enlarge overlay */
.enlarge-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.enlarge-card {
  background: #fff;
  border-radius: 6px 10px 6px 10px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  max-width: 90vw;
  max-height: 90vh;
  box-shadow: 0 8px 40px rgba(0,0,0,0.2);
}
.enlarge-img {
  border-radius: 4px 8px 4px 8px;
  border: 2px solid rgba(179, 158, 243,0.15);
  background-repeat: no-repeat;
  flex-shrink: 0;
}
.enlarge-info {
  font-size: 13px;
  line-height: 1.7;
  color: var(--app-text-secondary, var(--app-ink-muted));
  text-align: left;
  width: 100%;
}
.enlarge-info p {
  margin: 2px 0;
}
.enlarge-info strong {
  color: var(--app-text, var(--app-ink));
}
.enlarge-close {
  padding: 6px 24px;
  border: 3px solid var(--app-ink, #2d2d2d);
  border-radius: 4px 8px 4px 8px;
  background: #fff;
  color: var(--app-text, var(--app-ink));
  cursor: pointer;
  font-size: 14px;
}
</style>
