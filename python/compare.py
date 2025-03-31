import argparse
from math import log
from datetime import datetime
from tqdm import tqdm

import concurrent.futures

def open_file(file_path: str)-> str:
    with open(file_path,"r",encoding="utf-8") as f:
        return f.read()

def print_log(*args, **kwargs):
    now = datetime.now()
    print(now.strftime("%H:%M:%S:%f"), end=" ")
    print(*args, **kwargs)

def parse_database(text: str)-> list[tuple[str,str]]:
    sequences  = text.split("@")
    ret = []
    for seq in sequences[1:]:
        name = seq.split("\n")[0]
        sequence = "".join(seq.split("\n")[1:])
        ret.append((name,sequence))
    return ret

class Model: 
    def __init__(self, text: str, ko: int, alpha: float):
        self.ko = ko
        self.alpha = alpha
        self.alphabet = set(text)
        self.table = self.build_table(text)
        
    def build_table(self, text: str):
        table = {}
        for i in range(len(text) - self.ko):
            context = text[i:i+self.ko]
            next_char = text[i+self.ko]
            
            context_table, total = table.get(context,({},0))
            count = context_table.get(next_char,0)
            
            context_table[next_char] = count + 1
            table[context] = (context_table, total + 1)
            
        return table

    def estimate_bits(self, text: str)-> float:
        _sum = 0
        const_term = self.alpha * len(self.alphabet)
        for i in range(len(text) - self.ko):
            context = text[i:i+self.ko]
            next_char = text[i+self.ko]
            context_table, total = self.table.get(context,({},0))
            count = context_table.get(next_char,0)
            
            symbol_information = log(( count+self.alpha) / (total+const_term))
            _sum += symbol_information
            
        return -_sum/log(2)
    
    def nrc(self, x: str)-> float:
        content = self.estimate_bits(x)
        length_x = len(x)
        alphabet_x = set(x)
        return content / (length_x * log(len(alphabet_x),2)) 
    
def print_table(res, top):
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    HEADER_COLOR = "\033[93m"
    TOP_LEFT = "╔"
    TOP_RIGHT = "╗"
    BOTTOM_LEFT = "╚"
    BOTTOM_RIGHT = "╝"
    HORIZONTAL = "═"
    VERTICAL = "║"
    MID_LEFT = "╠"
    MID_RIGHT = "╣"
    MID_HORIZONTAL = "╬"
    TOP_MIDDLE = "╦"
    BOTTOM_MIDDLE = "╩"
    NRC_WIDTH = 6
    IDENTIFIER_WIDTH = 100

    # Print top border
    print(f"\n{TOP_LEFT}{HORIZONTAL * (NRC_WIDTH + 2)}{TOP_MIDDLE}{HORIZONTAL * (IDENTIFIER_WIDTH+2)}{TOP_RIGHT}")
    # Print header row
    header = f"{VERTICAL} {HEADER_COLOR}{BOLD}{'NRC':^{NRC_WIDTH}}{RESET} {VERTICAL} {HEADER_COLOR}{BOLD}{'Identifier':^{IDENTIFIER_WIDTH}}{RESET} {VERTICAL}"
    print(header)
    # Middle border
    print(f"{MID_LEFT}{HORIZONTAL * (NRC_WIDTH + 2)}{MID_HORIZONTAL}{HORIZONTAL * (IDENTIFIER_WIDTH+2)}{MID_RIGHT}")
    # Print table rows
    for i in range(top):
        if i >= len(res):
            break
        name, nrc = res[i]
        row = f"{VERTICAL} {CYAN}{nrc:.4f}{RESET} {VERTICAL} {name[:IDENTIFIER_WIDTH]:<{IDENTIFIER_WIDTH}} {VERTICAL}"
        print(row)
    # Print bottom border
    print(f"{BOTTOM_LEFT}{HORIZONTAL * (NRC_WIDTH + 2)}{BOTTOM_MIDDLE}{HORIZONTAL * (IDENTIFIER_WIDTH+2)}{BOTTOM_RIGHT}")

def main():
    parser = argparse.ArgumentParser(description="MetaClass: find similar sequences.")
    parser.add_argument("-d","--data", type=str, required=True, help="Database file")
    parser.add_argument("-s","--sequence", type=str, required=True, help="Sequence to compare")
    parser.add_argument("-k","--context", type=int, default=2 , help="Depth of the context")
    parser.add_argument("-a","--alpha", type=float, default=1.0 , help="Smoothing factor")
    parser.add_argument("-t","--top", type=int, default=20 , help="Top N similar sequences")
    parser.add_argument("-v","--verbose", action="store_true", help="Print verbose")
    
    args = parser.parse_args()
    
    database_text = open_file(args.data)
    sequences = parse_database(database_text)
    if args.verbose:
        print_log(f"[INFO] Database: loaded {len(sequences)} sequences")
    
    sequence_text = open_file(args.sequence)
    sequence_text = sequence_text.replace("\n","")

    model = Model(sequence_text, args.context, args.alpha)
    if args.verbose:
        print_log(f"[INFO] Model: created with depth {args.context} and alpha {args.alpha}")
        
    def compute_nrc(seq):
        return seq[0], model.nrc(seq[1]) 
    
    progress_bar = tqdm(total=len(sequences), desc="Processing NRCs", ncols=100)

    nrcs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(compute_nrc, seq): seq for seq in sequences}

        for future in concurrent.futures.as_completed(futures):
            nrcs.append(future.result())  
            progress_bar.update(1)  

    progress_bar.close()
    print("\033[F\033[K", end="") 
   
        
    nrcs.sort(key=lambda x: x[1])
    if args.verbose:
        print_log(f"[INFO] Similarity: calculated for {len(nrcs)} sequences")
        
    print_table(nrcs, args.top)
    
    return 

if __name__ == "__main__":
    main()