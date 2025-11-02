# Quick Start Guide - BPoW_Simulator

## All Issues Fixed! ✅

### What Was Fixed:
1. ✅ **No more KeyError** - Thread-safe event handling
2. ✅ **Blocks show as "Accepted"** - Not stale anymore
3. ✅ **Mining log updates** - Real-time event display
4. ✅ **Configure miners before start** - Set hash rates pre-simulation
5. ✅ **Computational power works** - Higher hash rate = more blocks
6. ✅ **Text is visible** - Black text on light backgrounds
7. ✅ **Beautiful UI** - Gradient blocks, purple container

---

## How to Run

### 1. Start the Simulator
```bash
streamlit run app.py
```

### 2. Configure Miners (BEFORE Starting)
1. Expand "⚡ Miner Computational Power (Hash Rates)"
2. Set hash rates for each miner:
   - Default: Miner 1=1000 H/s, Miner 2=2000 H/s, Miner 3=3000 H/s
   - Higher = More powerful = Mines faster
   - Example: Set Miner 3 to 5000 H/s to make it very powerful

### 3. Set Difficulty
- Use slider: 0 (easy) to 6 (insane)
- Recommendation: Start with 1-2 for quick testing

### 4. Start Simulation
- Click "▶️ Start Simulation"
- Watch blocks appear in real-time
- More powerful miners will mine more blocks

### 5. Observe
- **Genesis Block**: Block #0 with prev_hash = all zeros
- **Accepted Blocks**: Green with ✅
- **Mining Log**: Real-time updates
- **Block Chaining**: Each block's prev_hash matches previous block's hash

---

## What You'll See

### Blockchain View:
```
[Block #0] → [Block #1] → [Block #2] → [Block #3]
(Genesis)    (miner_3)    (miner_2)    (miner_3)
```

- **Purple gradient background** - Beautiful container
- **Green blocks** - Accepted (✅)
- **Black text** - Clearly visible
- **Hash values** - In white code boxes

### Mining Log:
```
[11:20:15] BLOCK_FOUND Block #3 found by miner_3
[11:20:13] BLOCK_FOUND Block #2 found by miner_2
[11:20:11] BLOCK_FOUND Block #1 found by miner_3
[11:20:10] SIMULATION_START Started simulation with 3 miners
```

### Metrics:
- Total Blocks
- Accepted Blocks
- Current Difficulty
- Average Block Time

---

## Common Scenarios

### Scenario 1: Test Computational Power
1. Set Miner 1 = 1000 H/s
2. Set Miner 2 = 5000 H/s (5x more powerful)
3. Set Miner 3 = 500 H/s
4. Start simulation
5. **Result**: Miner 2 will mine ~5x more blocks than Miner 3

### Scenario 2: Easy Mining (Quick Demo)
1. Set difficulty = 1
2. Set all miners to 2000+ H/s
3. **Result**: Blocks mine very fast

### Scenario 3: Realistic Mining
1. Set difficulty = 3-4
2. Use default miner rates
3. Enable "Use real SHA-256"
4. **Result**: Slower, more realistic mining

---

## Troubleshooting

### "No blocks mined yet..."
- **Solution**: Lower difficulty or increase hash rates

### Mining too fast?
- **Solution**: Increase difficulty or decrease hash rates

### Want to change miner power?
- **Solution**: Stop simulation, adjust rates, restart
- Note: Can only change BEFORE starting (realistic behavior)

---

## Technical Notes

### Hash Rates (Computational Power):
- Measured in H/s (hashes per second)
- Range: 100 - 10,000 H/s
- Default: Progressive (1000, 2000, 3000)
- Effect: delay = 1.0 / hash_rate seconds per attempt

### Difficulty:
- Level 0: No leading zeros (instant)
- Level 1: Hash starts with "0"
- Level 2: Hash starts with "00"
- Level 4: Hash starts with "0000"
- etc.

### Genesis Block:
- Always Block #0
- Miner: "genesis"
- prev_hash: "0000...0000" (64 zeros)
- Automatically created on simulation start

---

## Testing

### Quick Validation:
1. Start simulation
2. Check: ✅ No KeyError in console
3. Check: ✅ Blocks show green "Accepted"
4. Check: ✅ Mining log updates
5. Check: ✅ Genesis block visible as Block #0
6. Check: ✅ All text is black/visible

### Run Tests:
```bash
python tests/test_integration.py
```

---

## Features Working:

✅ Thread-safe event handling (no crashes)  
✅ Real SHA256 or fast simulation mode  
✅ Configurable miner computational power  
✅ Difficulty-based Proof-of-Work  
✅ Genesis block with all-zero prev_hash  
✅ Proper block chaining  
✅ Real-time mining log  
✅ Block status visualization  
✅ Beautiful gradient UI  
✅ Timestamp validation  
✅ Thread-safe concurrent mining  

Enjoy your blockchain simulator! 🎉
