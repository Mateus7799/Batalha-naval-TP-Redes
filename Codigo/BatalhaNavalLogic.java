/**
 * Classe que gerencia a lógica do jogo Batalha Naval
 * Controla os tabuleiros, validação de jogadas e sistema de turnos
 */
public class BatalhaNavalLogic {
    // === CONSTANTES DO JOGO ===
    private static final int TAMANHO_TABULEIRO = 10;

    // Estados das células do tabuleiro
    private static final int AGUA = 0;      // Célula vazia (não atacada)
    private static final int NAVIO = 1;     // Célula com navio
    private static final int ACERTO = 2;    // Célula atacada com acerto
    private static final int ERRO = 3;      // Célula atacada com erro

    // === PROTOCOLO DE COMUNICAÇÃO (para multiplayer via Socket) ===
    // Formato: COMANDO;parametro1;parametro2
    public static final String NET_TIRO = "TIRO";           // Ex: TIRO;4;5
    public static final String NET_RESULTADO = "RES";       // Ex: RES;ACERTO ou RES;ERRO
    public static final String NET_TURNO = "TURNO";         // Sincronização de turno
    public static final String NET_ACERTO = "ACERTO";       // Resultado: acertou
    public static final String NET_ERRO = "ERRO";           // Resultado: errou

    private int[][] meuTabuleiro;           // Meus navios
    private int[][] tabuleiroInimigo;       // Navios do inimigo (desconhecidos)
    private int[][] estadoTabuleinoMeu;     // Histórico dos ataques sofridos (para mostrar ao jogador)
    private int[][] estadoTabuleiroInimigo; // Histórico dos meus ataques

    private boolean minhaVez;
    private int naviosDestruidos;
    private int naviosInimigosDestruidos;

    public BatalhaNavalLogic() {
        inicializarTabuleiros();
    }

    private void inicializarTabuleiros() {
        meuTabuleiro = new int[TAMANHO_TABULEIRO][TAMANHO_TABULEIRO];
        tabuleiroInimigo = new int[TAMANHO_TABULEIRO][TAMANHO_TABULEIRO];
        estadoTabuleinoMeu = new int[TAMANHO_TABULEIRO][TAMANHO_TABULEIRO];
        estadoTabuleiroInimigo = new int[TAMANHO_TABULEIRO][TAMANHO_TABULEIRO];

        preencherComAgua(meuTabuleiro);
        preencherComAgua(tabuleiroInimigo);
        preencherComAgua(estadoTabuleinoMeu);
        preencherComAgua(estadoTabuleiroInimigo);

        minhaVez = true;
        naviosDestruidos = 0;
        naviosInimigosDestruidos = 0;
    }

    private void preencherComAgua(int[][] tabuleiro) {
        for (int i = 0; i < TAMANHO_TABULEIRO; i++) {
            for (int j = 0; j < TAMANHO_TABULEIRO; j++) {
                tabuleiro[i][j] = AGUA;
            }
        }
    }

    /**
     * Posiciona um navio no meu tabuleiro
     * @param linha Linha inicial do navio
     * @param coluna Coluna inicial do navio
     * @param tamanho Tamanho do navio
     * @param horizontal true para horizontal, false para vertical
     * @return true se foi posicionado com sucesso
     */
    public boolean posicionarNavio(int linha, int coluna, int tamanho, boolean horizontal) {
        if (!validarPosicaoNavio(linha, coluna, tamanho, horizontal, meuTabuleiro)) {
            return false;
        }

        if (horizontal) {
            for (int j = coluna; j < coluna + tamanho; j++) {
                meuTabuleiro[linha][j] = NAVIO;
            }
        } else {
            for (int i = linha; i < linha + tamanho; i++) {
                meuTabuleiro[i][coluna] = NAVIO;
            }
        }

        return true;
    }

    /**
     * Posiciona um navio no tabuleiro do inimigo
     * @param linha Linha inicial do navio
     * @param coluna Coluna inicial do navio
     * @param tamanho Tamanho do navio
     * @param horizontal true para horizontal, false para vertical
     * @return true se foi posicionado com sucesso
     */
    public boolean posicionarNavioInimigo(int linha, int coluna, int tamanho, boolean horizontal) {
        if (!validarPosicaoNavio(linha, coluna, tamanho, horizontal, tabuleiroInimigo)) {
            return false;
        }

        if (horizontal) {
            for (int j = coluna; j < coluna + tamanho; j++) {
                tabuleiroInimigo[linha][j] = NAVIO;
            }
        } else {
            for (int i = linha; i < linha + tamanho; i++) {
                tabuleiroInimigo[i][coluna] = NAVIO;
            }
        }

        return true;
    }

    private boolean validarPosicaoNavio(int linha, int coluna, int tamanho, boolean horizontal, int[][] tabuleiro) {
        if (horizontal) {
            if (coluna + tamanho > TAMANHO_TABULEIRO) return false;
            for (int j = coluna; j < coluna + tamanho; j++) {
                if (tabuleiro[linha][j] != AGUA) return false;
            }
        } else {
            if (linha + tamanho > TAMANHO_TABULEIRO) return false;
            for (int i = linha; i < linha + tamanho; i++) {
                if (tabuleiro[i][coluna] != AGUA) return false;
            }
        }
        return true;
    }

    /**
     * Verifica a jogada na posição indicada
     * @param linha Linha do ataque
     * @param coluna Coluna do ataque
     * @return 0 para erro, 1 para acerto, -1 para jogada inválida
     */
    public int verificarJogada(int linha, int coluna) {
        if (estadoTabuleiroInimigo[linha][coluna] != AGUA) {
            return -1; // Já foi atacado
        }

        if (tabuleiroInimigo[linha][coluna] == NAVIO) {
            estadoTabuleiroInimigo[linha][coluna] = ACERTO;
            naviosInimigosDestruidos++;
            System.out.println("[LOCAL] Acerto em (" + linha + ", " + coluna + ")!");
            return 1; // Acerto
        } else {
            estadoTabuleiroInimigo[linha][coluna] = ERRO;
            System.out.println("[LOCAL] Erro em (" + linha + ", " + coluna + ")!");
            return 0; // Erro
        }
    }

    /**
     * Simula o turno do inimigo (com IA aleatória)
     * TODO: Substituir lógica de IA por recebimento de coordenadas via Socket
     * Este método será removido quando implementar multiplayer via rede.
     * A IA aqui é apenas para teste local do jogo.
     */
    public void turnoInimigo() {
        // TODO: Quando multiplayer estiver ativo, receber coordenadas via receberJogadaSocket()
        // por enquanto, geramos aleatoriamente para testes locais

        int linha, coluna;
        boolean posicaoValida;

        do {
            linha = (int) (Math.random() * TAMANHO_TABULEIRO);
            coluna = (int) (Math.random() * TAMANHO_TABULEIRO);
            posicaoValida = estadoTabuleinoMeu[linha][coluna] == AGUA;
        } while (!posicaoValida);

        if (meuTabuleiro[linha][coluna] == NAVIO) {
            estadoTabuleinoMeu[linha][coluna] = ACERTO;
            naviosDestruidos++;
            System.out.println("[IA LOCAL] Acertou em (" + linha + ", " + coluna + ")!");
        } else {
            estadoTabuleinoMeu[linha][coluna] = ERRO;
            System.out.println("[IA LOCAL] Errou em (" + linha + ", " + coluna + ")!");
        }
    }

    // Placeholder para enviar jogada via Socket
    public void enviarJogadaSocket(int linha, int coluna) {
        System.out.println("[SOCKET] Enviando jogada: (" + linha + ", " + coluna + ")");
        // TODO: Implementar envio via Socket quando conectar em rede
    }

    // Placeholder para receber jogada via Socket
    public void receberJogadaSocket() {
        System.out.println("[SOCKET] Aguardando jogada do adversário...");
        // TODO: Implementar recebimento via Socket quando conectar em rede
    }

    public int[][] getMeuTabuleiro() {
        return meuTabuleiro;
    }

    public int[][] getTabuleiroInimigo() {
        return tabuleiroInimigo;
    }

    public int[][] getEstadoTabuleinoMeu() {
        return estadoTabuleinoMeu;
    }

    public int[][] getEstadoTabuleiroInimigo() {
        return estadoTabuleiroInimigo;
    }

    public boolean isMinhaVez() {
        return minhaVez;
    }

    public void setMinhaVez(boolean minhaVez) {
        this.minhaVez = minhaVez;
    }

    public int getNaviosDestruidos() {
        return naviosDestruidos;
    }

    public int getNaviosInimigosDestruidos() {
        return naviosInimigosDestruidos;
    }

    public boolean verificarVitoria() {
        return naviosInimigosDestruidos >= 17; // 17 células de navios
    }

    public boolean verificarDerrota() {
        return naviosDestruidos >= 17;
    }

    public static int getTamanhoDaTabuleiro() {
        return TAMANHO_TABULEIRO;
    }

    public static int getAGUA() {
        return AGUA;
    }

    public static int getNAVIO() {
        return NAVIO;
    }

    public static int getACERTO() {
        return ACERTO;
    }

    public static int getERRO() {
        return ERRO;
    }
}
