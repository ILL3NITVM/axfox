(() => {
  'use strict';

  const BSC_CHAIN_ID = '0x38';
  const AXFOX_TOKEN = '0x3ABFBDf7a12Cb7589a330A293e91380f84A94444';
  const BSC_RPC = 'https://bsc-dataseed.bnbchain.org';
  const BSC_EXPLORER = 'https://bscscan.com';
  let currentAccount = null;
  let preparedTx = null;

  const $ = (id) => document.getElementById(id);
  const setStatus = (msg, kind = '') => {
    const el = $('wallet-status');
    if (!el) return;
    el.textContent = msg;
    el.className = `wallet-status ${kind}`.trim();
  };

  const short = (addr) => addr ? `${addr.slice(0, 6)}…${addr.slice(-4)}` : 'not connected';

  function provider() {
    return window.ethereum || null;
  }

  async function ensureBsc() {
    const eth = provider();
    if (!eth) throw new Error('No EIP-1193 wallet detected. Open this site inside MetaMask or another compatible wallet browser.');
    const chainId = await eth.request({ method: 'eth_chainId' });
    if (chainId === BSC_CHAIN_ID) return;
    try {
      await eth.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: BSC_CHAIN_ID }],
      });
    } catch (err) {
      if (err && Number(err.code) === 4902) {
        await eth.request({
          method: 'wallet_addEthereumChain',
          params: [{
            chainId: BSC_CHAIN_ID,
            chainName: 'BNB Smart Chain',
            nativeCurrency: { name: 'BNB', symbol: 'BNB', decimals: 18 },
            rpcUrls: [BSC_RPC],
            blockExplorerUrls: [BSC_EXPLORER],
          }],
        });
      } else {
        throw err;
      }
    }
  }

  async function connect() {
    const eth = provider();
    if (!eth) {
      setStatus('No compatible wallet detected. Open axfox.quadproxy.com inside MetaMask mobile or a browser with an EIP-1193 wallet.', 'warn');
      return;
    }
    setStatus('Requesting wallet connection…');
    const accounts = await eth.request({ method: 'eth_requestAccounts' });
    currentAccount = accounts && accounts[0] ? accounts[0] : null;
    if (!currentAccount) throw new Error('Wallet returned no account.');
    await ensureBsc();
    $('wallet-account').textContent = currentAccount;
    setStatus(`Connected ${short(currentAccount)} on BNB Smart Chain.`, 'ok');
  }

  async function signProof() {
    if (!currentAccount) await connect();
    const eth = provider();
    const nonce = crypto.getRandomValues(new Uint32Array(4)).join('-');
    const message = [
      'AXFOX wallet ownership proof',
      `Domain: ${location.host}`,
      `Address: ${currentAccount}`,
      `Issued: ${new Date().toISOString()}`,
      `Nonce: ${nonce}`,
      '',
      'This signature does not transfer BNB or tokens.',
    ].join('\n');
    setStatus('Review the message in your wallet before signing…');
    const signature = await eth.request({
      method: 'personal_sign',
      params: [message, currentAccount],
    });
    $('signature-output').textContent = signature;
    setStatus('Message signed. No transaction was broadcast.', 'ok');
  }

  function decimalBnbToWeiHex(input) {
    const s = String(input || '').trim();
    if (!/^\d+(?:\.\d{0,18})?$/.test(s)) throw new Error('BNB value must be a non-negative decimal with at most 18 decimal places.');
    const [whole, frac = ''] = s.split('.');
    const wei = BigInt(whole) * 10n ** 18n + BigInt((frac.padEnd(18, '0') || '0'));
    return `0x${wei.toString(16)}`;
  }

  function validateAddress(addr) {
    return /^0x[a-fA-F0-9]{40}$/.test(addr);
  }

  function validateData(data) {
    return /^0x(?:[a-fA-F0-9]{2})*$/.test(data);
  }

  function prepareTransaction() {
    if (!currentAccount) throw new Error('Connect a wallet first.');
    const to = $('tx-to').value.trim();
    const valueInput = $('tx-value').value.trim() || '0';
    const data = $('tx-data').value.trim() || '0x';

    if (!validateAddress(to)) throw new Error('Destination must be a valid 0x address.');
    if (!validateData(data)) throw new Error('Transaction data must be 0x-prefixed even-length hexadecimal.');

    preparedTx = {
      from: currentAccount,
      to,
      value: decimalBnbToWeiHex(valueInput),
      data,
      chainId: BSC_CHAIN_ID,
    };

    $('tx-preview').textContent = JSON.stringify({
      network: 'BNB Smart Chain (56)',
      from: currentAccount,
      to,
      valueBNB: valueInput,
      valueWeiHex: preparedTx.value,
      data,
    }, null, 2);
    $('tx-confirm').value = '';
    setStatus('Transaction prepared locally. Nothing has been signed or sent.', 'ok');
  }

  async function sendTransaction() {
    if (!preparedTx) throw new Error('Prepare and review the transaction first.');
    if ($('tx-confirm').value.trim().toUpperCase() !== 'SEND') {
      throw new Error('Type SEND in the confirmation box after reviewing destination, BNB value, and data.');
    }
    await ensureBsc();
    const eth = provider();
    setStatus('Wallet signature requested. Verify destination, value, gas and data in your wallet before approving…', 'warn');
    const txHash = await eth.request({
      method: 'eth_sendTransaction',
      params: [preparedTx],
    });
    $('tx-result').innerHTML = `<a href="${BSC_EXPLORER}/tx/${txHash}" target="_blank" rel="noopener">${txHash}</a>`;
    setStatus('Transaction signed by your wallet and submitted to BNB Smart Chain.', 'ok');
    preparedTx = null;
    $('tx-confirm').value = '';
  }

  async function readTokenDecimals() {
    const eth = provider();
    // ERC-20 decimals() selector = 0x313ce567. Read from the token itself instead
    // of hard-coding token metadata into the wallet request.
    const raw = await eth.request({
      method: 'eth_call',
      params: [{ to: AXFOX_TOKEN, data: '0x313ce567' }, 'latest'],
    });
    if (!/^0x[0-9a-fA-F]+$/.test(raw || '')) throw new Error('Could not read AXFOX decimals from chain.');
    const decimals = Number(BigInt(raw));
    if (!Number.isInteger(decimals) || decimals < 0 || decimals > 255) throw new Error('AXFOX decimals response was invalid.');
    return decimals;
  }

  async function watchAxfox() {
    const eth = provider();
    if (!eth) throw new Error('No compatible wallet detected.');
    await ensureBsc();
    const decimals = await readTokenDecimals();
    const ok = await eth.request({
      method: 'wallet_watchAsset',
      params: {
        type: 'ERC20',
        options: {
          address: AXFOX_TOKEN,
          symbol: 'AXFOX',
          decimals,
          image: `${location.origin}/logo.png`,
        },
      },
    });
    setStatus(ok ? 'AXFOX token request accepted by wallet.' : 'Wallet did not add AXFOX.', ok ? 'ok' : 'warn');
  }

  function bind(id, fn) {
    const el = $(id);
    if (!el) return;
    el.addEventListener('click', async () => {
      try { await fn(); }
      catch (err) {
        const msg = err && err.message ? err.message : String(err);
        setStatus(msg, Number(err && err.code) === 4001 ? 'warn' : 'error');
      }
    });
  }

  function init() {
    bind('wallet-connect', connect);
    bind('wallet-switch', ensureBsc);
    bind('wallet-sign-proof', signProof);
    bind('wallet-watch-asset', watchAxfox);
    bind('tx-prepare', prepareTransaction);
    bind('tx-send', sendTransaction);

    const eth = provider();
    if (!eth) {
      setStatus('No injected wallet detected. Read-only AXFOX data still works; signing requires MetaMask or another compatible wallet.', 'warn');
      return;
    }

    eth.on?.('accountsChanged', (accounts) => {
      currentAccount = accounts && accounts[0] ? accounts[0] : null;
      if ($('wallet-account')) $('wallet-account').textContent = currentAccount || 'not connected';
      setStatus(currentAccount ? `Account changed to ${short(currentAccount)}.` : 'Wallet disconnected.', currentAccount ? 'ok' : 'warn');
      preparedTx = null;
    });

    eth.on?.('chainChanged', (chainId) => {
      setStatus(chainId === BSC_CHAIN_ID ? 'BNB Smart Chain selected.' : `Wrong network (${chainId}). Switch to BNB Smart Chain before signing.`, chainId === BSC_CHAIN_ID ? 'ok' : 'warn');
      preparedTx = null;
    });

    eth.request({ method: 'eth_accounts' }).then((accounts) => {
      currentAccount = accounts && accounts[0] ? accounts[0] : null;
      if ($('wallet-account')) $('wallet-account').textContent = currentAccount || 'not connected';
      if (currentAccount) setStatus(`Wallet available: ${short(currentAccount)}.`, 'ok');
    }).catch(() => {});
  }

  document.addEventListener('DOMContentLoaded', init);
})();
