### **1 Introduction**

Since their invention, the Transformer (Vaswani et al., 2017), and more specifically the decoder-only
Transformers used originally for the GPT series of models (Radford et al., 2018), have become the core
components of AI systems.


It is remarkable that, after almost a decade, and in spite of improvements on many aspects of this class of
methods, the autoregressive modelling of Transformers remains essentially unchallenged. We propose in
this paper to revisit this key design aspect by allowing richer and more natural density models to emerge:


  - We extend the auto-regressive model of the decoder Transformer by allowing the conditioning on
latent variables, thanks to a formulation as a conditional Variational Autoencoder (§ 3.1).


  - We propose an implementation that requires a very modest computational and memory usage
overhead (§ 3.2).


The benefits of the proposed method are shown by training 1.5B and 8B models from scratch and assessing
performance on multiple downstream benchmarks (§ 4).

### **2 Motivation**


Decoder Transformers are auto-regressive discrete density approximators. They model a sequence of
tokens _S_ 1 _, . . ., ST_ by estimating the conditional distribution of each given those preceding it. Sampling is
done by generating one token after another, each time computing the distribution of the next symbol
given those generated so far.


The only density modelling and sampling that such models implement is that of the generated tokens. In
particular, a decoder Transformer does not make additional latent decisions about the stream of symbols
to generate. Its only decisions are the choices of the tokens themselves.


Consider, for instance, that we train such a model to generate movie reviews and that we want to have
two clearly separated categories of negative and positive reviews. Given a large enough model and the
necessary amount of training data, there is no doubt that a decoder Transformer trained on a dataset
of that form would work perfectly and would generate these two types of reviews. However, to do so, it
would generate tokens one after another and decide, based on the words generated so far, whether the
review it is currently generating is a positive or a negative one, and continue the process accordingly. In
particular, _the model would not make the explicit decision to generate a negative or a positive review_ . It
would produce tokens, and this notion of a negative or positive review would be implicit in their posterior
probabilities.


Due to the chain rule, any density can be modelled as autoregressive. However, in particular when the


1


“natural” structure involves conditioning on latent variables, the autoregressive model of the signal may be
a great deal more complex than the full joint model including the latent.


We can consider a simple example illustrating that point. Let _Z ∼B_ (0 _._ 5) be a latent “coin flip”, and
_X_ 1 _, . . ., XT_ be equal to _Z_ with independent flips of probability _ϵ_ .


The _Xt_ s are conditionally independent given _Z_, and we have


_P_ ( _Xt_ +1 = 1 _| Z_ = _z_ ) = _ϵz_ + (1 _−_ _ϵ_ )(1 _−_ _z_ ) (1)


however, expressed as an auto-regressive model without _Z_, we get:



_P_ ( _Xt_ +1 = 1 _| X_ 1 = _x_ 1 _, . . ., Xt_ = _xt_ ) =




- 1 _−ϵ_ _ϵ_ - [�] _s_ _[t]_ =1 _[x][s]_ (1 _−_ _ϵ_ ) _[t]_ [+1] + - 1 _−ϵ_ _ϵ_




~~�~~ 1 _−ϵ_ _ϵ_ ~~�~~ ~~[�]~~ _s_ _[t]_ =1 _[x][s]_ (1 _−_ _ϵ_ ) _[t]_ + - 1 _−ϵ_ _ϵ_



_−ϵ_ - [�] _s_ _[t]_ =1 _[x][s]_ _t_ +1

_ϵ_ _ϵ_



_._ (2)

_−ϵ_ _ϵ_ - ~~[�]~~ _s_ _[t]_ =1 _[x][s]_ _ϵt_



We could easily come with worse examples when expressed autoregressively, for instance when the latent
variables are positions in the sequence, e.g. the index where a certain pattern occurs as in the example of
§ 4.1. What we observe in such cases is that it requires running estimates of probabilities (“probability
that the target appears here”) for which estimation errors are unavoidable and problematic.


The consequence is that a purely auto-regressive density model suffers potentially from several drawbacks:


  - It requires an unnecessarily complicated computation, and greater capacity, to implicitly make
post-hoc decisions or infer latent quantities from the generated tokens.


  - It may be sent off track during the process if, by mistake, a few tokens generated are erroneous,
ambiguous or contradictory with those generated previously.


  - Key concepts do not appear spontaneously due to the "natural" factorization of the distribution,
but are built post-hoc by necessity to fit the training samples better. This may be a fundamental
weakness when operating out of distribution.


The main objective of the present work is to address these issues by providing the model with the freedom
of conditioning its auto-regressive process on latent random quantities that are not imposed by the training
examples.


For instance, for the review generator example above, the model could use a random Boolean value to
decide once for all whether the tokens it produces are from the distribution of negative or positive reviews,
removing the need for a complicated posterior estimate from the tokens already generated.

### **3 Method**


Any latent random value _Yr_, whatever its statistical dependency with the tokens _S_ 1 _, . . ., St_ and other latent
_Y_ 1 _, . . ., Yr−_ 1 sampled so far, can be expressed under reasonable assumptions as _fr_ ( _S_ 1 _, . . ., St, Y_ 1 _, . . ., Yr−_ 1 _, Zr_ )
where _Zr_ is a value coming from a random generator.


Hence, if we provide the model with enough random values _Z_ 1 _, Z_ 2 _, . . ._ sampled independently during
generation, a proper training procedure could in principle build families of latent variables with arbitrary
dependency structure, as long as the model’s capacity allows it to encode _fr_ .


In the same way that the choice of a token during sampling can be expressed as a function of a random
value and the logits, any activation which is a function of a random value and other activations can be
interpreted as a decision made by the model during the generative process. Such decisions make the
latent activation non-deterministic functions of the tokens, and observing the latter only gives a partial
information about the former.


2


_P_ ˆ( _S_ 2: _T_ )

|Col1|Col2|
|---|---|
|Dec|Dec|
|||



_S_ 1: _T −_ 1


(a)



_P_ ˆ( _S_ 2: _T_ )

|Col1|Col2|Col3|
|---|---|---|
|Dec|Dec|Dec|
|_Z_|_Z_||



_S_ 1: _T −_ 1



_P_ ˆ( _S_ 2: _T_ )


_S_ 1: _T −_ 1


(b)



_P_ ˆ( _S_ 2: _T_ )



|Col1|Col2|
|---|---|
|Dec 2/2|Dec 2/2|
|_Z_|_Z_|
|Dec 1/2|Dec 1/2|
|||


_S_ 1: _T −_ 1



(c)



_P_ ˆ( _S_ 2: _T_ )









_S_ 1: _T −_ 1



**Figure 1** A standard decoder Transformer (a) can be extended to utilize a random state _Z_ in inference (b, left), in
which case it has to be trained as a conditional VAE with an encoder (b, right). The Free Transformer (c) reduces
the overhead of the encoder by having the random state _Z_ injected in its middle layer (c, left), and using for
encoder during training the combination of its first half combined with one non-causal layer specific to the encoder
(c, right). See Figure 2 for a detailed depiction of that architecture.


**3.1** **Conditional Variational Autoencoder**


Generating a full sequence from scratch with a model that depends on a random variable _Z_ is trivial:
sample _Z ∼_ _P_ ( _Z_ ) and then run the standard auto-regressive process, with the computation of the logits
modulated by _Z_ .


Training the model, however, is far more involved. Given a training sample _S_, the objective is to maximize


                 _P_ ( _S_ ) = _P_ ( _S | Z_ = _z_ ) _P_ ( _Z_ = _z_ ) _dz,_ (3)

_z_


which can be estimated only if we can get _Z_ s consistent with _S_, which amounts to a complex inference
problem if we want _Z_ to capture meaningful structural properties of the sequence.


Providing those _Z_ s is the role of the encoder of a Variational Autoencoder (Kingma and Welling, 2013),
whose main purpose is to sample from a “good” distribution _Q_ ( _Z | S_ ) so that a sampled _Z_ modulates the
decoder in a way that leads it to generate _S_ .


We follow this approach and optimize jointly the parameters of the decoder and the parameters of a
second model, which is an encoder in the VAE sense.


Even though the noise _Z_ has no relation to _S_ initially, if the training succeeds, the model will use it to
structure the generative process. In the example of a movie review generator of the previous section,
for instance, given a review from the training set, the encoder would implicitly classify it as positive or
negative, and generate a consistent _Z_ . Increasing _P_ ( _S | Z_ ) with that _Z_ could be interpreted as improving
the “negative review generator” or the “positive review generator” that are implicitly encoded in the
decoder’s weights.


A key element of this approach is to limit the amount of information flowing from the encoder to the
decoder through _Z_, so that the encoder does not provide quantities that should be computed by the
decoder. At the limit the encoder could copy entirely _S_ into _Z_ so that a trivial decoder, useless without
the encoder, hence in inference, would score perfectly in training.


The formal derivation of the VAE shows that the proper measure of information is the Kullback-Leibler
divergence between _Q_ ( _Z | S_ ) and _P_ ( _Z_ ), and that the loss to minimize should sum it with the reconstruction


3


**Figure 2** The Free Transformer. We omit the normalization layers and residual connections from the model and the
batch size from the tensor shapes for clarity. The operators in orange are specific to the encoder and are evaluated
only for training or KV cache pre-filling, those with a dashed contour have no trainable parameters. The Binary
Mapper is described in § 3.4. During generation, the encoder is not evaluated and _Z_ is sampled uniformly among
the one-hot vectors of dimension 2 _[H]_ .


4


**Algorithm 1** Forward pass of a standard decoder Transformer

1: **procedure** Forward( _tokens_ )
2: _x ←_ embeddings( _tokens_ )
3: **for** _n_ = 1 _, . . ., B_ **do**

4: _x ←_ blocks[ _n_ ]( _in_ = _x_ )
5: **end for**
6: _logits ←_ linear_readout(RMS_norm( _x_ ))
7: **return** _logits_
8: **end procedure**


loss, which here is the usual cross-entropy.


**3.2** **Model structure**


In what follows, we call “Transformer Block” the usual combination of a Multi-Head Attention layer and a
MLP-like tokenwise module, with normalisation layers and residual connections.


As pictured on Figure 1 and 2, the Free Transformer is a standard decoder with a noise _Z_ injected in its
middle layer. This allows to share half of the Transformer block with the encoder, cutting down drastically
the computational overhead by having a single Transformer block that has to be computed specifically for
the encoder. Hence, as we will see, this model possesses all the components of a decoder Transformer and
has an additional non-causal block and two linear layers for the encoder. While we did not investigate
what is the best depth to inject _Z_, doing it too early would reduce the encoder’s capacity, and doing it
too late would reduce the decoder’s capacity to process the latent variables.


For clarity, we omit in what follows the batch size in the tensor shapes.


As a standard decoder Transformer, the Free Transformer processes a sequence of tokens by first encoding
them with the embedding table into a tensor _X_ 0 of shape _T × D_ .


Then it evaluates sequentially the first _L/_ 2 Transformer blocks to get _XL/_ 2 of same shape, and at this
point, it samples a sequence of one-hot vectors _Z_ = ( _Z_ 1 _, . . ., Zt_ ) _∈{_ 0 _,_ 1 _}_ _[T][ ×][C]_ . During generation, this is
done by sampling, for each _Zt_, an index _c_ uniformly in _{_ 0 _, . . ., C −_ 1 _}_, and then encoding it as a one-hot
vector of dimension _C_ . During training or KV cache pre-filling, _Z_ has to be consistent with the tokens of
_S_ already fixed, and the sampling is done with the encoder instead, as described in § 3.3.


This tensor _Z_ is processed by a linear layer to obtain a tensor _R_ of shape _T × D_ . Then, the _L/_ 2 + 1th
Transformer block gets as input for queries the tensor _XL/_ 2 and as input for keys and values the tensor
_XL/_ 2 + _R_ . The rest of the Transformer blocks are evaluated in sequence to get _XL_ which is processed by
the read-out linear layer to obtain the logit tensor _L_ of shape _T × V_, where _V_ is the vocabulary suze.


**3.3** **Encoder and Loss**


As stated in the previous section, during training or KV cache pre-filling, the tensor _Z_ is sampled with
the encoder.


The Free Transformer possesses one Transformer block specific to the encoder, which is non-causal,
making the encoder as a whole non-causal. This is necessary since the conditioning by the decoder may
have long-range effects, requiring the full sequence to be taken into account to get a proper conditional
distribution of the latent.


This encoder-specific block gets as input for the queries a trained token embedding _ζ_ replicated to match
the sequence length, and for the keys and values the output of the first half of the decoder’s blocks. The
motivation for using a learned constant input for the queries instead of the standard representation of the
input sequence is to prevent the encoder from building a token-wise mapping and make it instead capture
global properties of the sequence that may be more transferable across tasks and data-sets.


A linear readout computes from the encoder block’s output a vector of dimension _H_ = 16 for every token.


5


**Algorithm 2** Forward pass of a Free Transformer

1: **procedure** Forward( _tokens_ )
2: _x ←_ embeddings( _tokens_ )
3: **for** _n_ = 1 _, . . ., B/_ 2 **do**

4: _x ←_ blocks[ _n_ ]( _in_ = _x_ )
5: **end for**
6: **if** _train_ or _prefill_ **then**
7: _y ←_ encoder_block( _in_ _ _q_ = _zeta, in_ _ _kv_ = _x_ )
8: _o ←_ encoder_linear_readout(RMS_norm( _y_ ))
9: _z ←_ binary_mapper( _o_ )

10: **else**
11: _z ←_ one_hot(uniform_sampler())
12: **end if**
13: _r ←_ linear_post_sampler( _z_ )
14: _x ←_ blocks[ _B/_ 2 + 1]( _in_ _ _q_ = _x, in_ _ _kv_ = _x_ + _r_ )
15: **for** _n_ = _B/_ 2 + 1 _, . . ., B_ **do**

16: _x ←_ blocks[ _n_ ]( _in_ = _x_ )
17: **end for**
18: _logits ←_ linear_readout(RMS_norm( _x_ ))
19: **return** _logits_
20: **end procedure**


These components are interpreted as logits of individual bit, used to sample a value in _{_ 0 _, . . .,_ 2 _[H]_ _−_ 1 _}_
which is encoded into a one-hot vector of dimension 2 _[H]_ = 65 _,_ 536, with gradient pass-through, as described
in § 3.4.


Hence, the random embedding _Z_ is a sequence of _T_ one-hot vectors _Zt_ of dimension 2 _[H]_ . The prior
distribution used for generation is uniform _P_ ( _Zt_ = _z_ ) = 1 _/_ 2 _[H]_, and _Q_ ( _Z | S_ = _s_ ) is the distribution
corresponding to the sampling with the encoder described above. The KL divergence is then equal to




  -  DKL _Q_ ( _Zt | S_ 1 _, . . ., ST_ ) _P_ ( _Zt_ ) = _H_ log 2 +
���



2 _[H]_

- _Q_ ( _Z_ = _z | S_ ) log _Q_ ( _Z_ = _z | S_ ) _._ (4)


_z_ =1



We control it by adding it to the loss, and prevent its collapse by using a token-wise free bits method
(Kingma et al., 2016). This means that we sum the KL divergence of individual _Zt_ that are above a
threshold _κ_ and ignore the others.


This leads us to use for training loss the sum of the standard cross-entropy and the following quantity



1

_T_



_T_

- max �0 _,_ DKL� _Q_ ( _Zt | S_ 1 _, . . ., ST_ ) _P_ ( _Zt_ )� _−_ _κ_ - _,_ (5)

���
_t_ =1



where the threshold _κ_ is an hyperparameter.


**3.4** **Binary Mapper**


The last linear layer of the encoder computes for every index _t_ of the sequence being processed a vector
_Lt_ = ( _Lt,_ 1 _, . . ., Lt,H_ ) _∈_ R _[H]_, whose components are interpreted as the logits of individual bits of a binary
encoding.


The Binary Mapper samples those bits _Bt,_ 1 _, . . ., Bt,H_ independentely with


1
_P_ ( _Bt,h_ = 1) = 1 + _e_ _[−][L][t,h]_ _[,]_ (6)


and outputs a one-hot vector _Yt_ of dimension 2 _[H]_ corresponding to the resulting value:

_Yt,d_ =                   - 1 if _d_ = 1 + [�] _h_ _[H]_ =1 [2] _[h][−]_ [1] _[B][h,t]_ (7)
0 otherwise.


6


During training, the computation also propagates the gradient of the probabilities of the 2 _[H]_ values. If
_U_ ( _d_ ) = ( _U_ 1( _d_ ) _, . . ., UH_ ( _d_ )) _∈{_ 0 _,_ 1 _}_ _[H]_ is the binary encoding of _d_, and we define _Gt_ as


_Gt,d_ = _P_ ( _Bt_ = _U_ ( _d −_ 1))







= exp


= exp



��



�� - 1

(1 _−_ _Uh_ ( _d −_ 1)) log 1 _−_
1 + _e_ _[−][L][t,h]_
_h_



log _P_ ( _Bt,h_ = _Uh_ ( _d −_ 1))

_h_




- - 1
+ _Uh_ ( _d −_ 1) log
1 + _e_ _[−][L][t,h]_



_,_




- [�]



then the Binary Mapper outputs
_Yt,d_ + _Gt,d −_ detach( _Gt,d_ ) _,_ (8)


where _∀x,_ detach( _x_ ) = _x_ and _J_ detach( _x_ ) = 0.


The motivation for using a binary encoding instead of having the encoder output 2 _[H]_ logits directly is to
facilitate the gradient pass-through thanks to the monotonicity of the sigmoid.

### **4 Experiments**


We first test the qualitative behavior of the Free Transformer on a synthetic task in § 4.1, then compare
it on multiple benchmarks to baselines with 1.5B and 8B parameters models for various KL divergence
thresholds in § 4.4, and finally assess the performance gain of a 8B parameter model trained on 1T tokens
in § 4.5.


**4.1** **Synthetic Dataset**


To confirm that the Free Transformer indeed utilizes _Z_ to condition its generative process, we designed a
synthetic dataset and trained a small Free Transformer with different free-bits thresholds. Doing so allows
to observe what aspects of the modeling are packed by the encoder in _Z_ .


Each sequence in our synthetic training set is generated as follows:


  - start with a string of 64 underscores “_”,


  - pick an upper case letter and a position in the sequence at random, and replace the underscores
there with a “target” made of the selected letter repeated 8 times,


  - replace any character with an exclamation mark with probability 1 _/_ 16


  - concatenate a prompt made of the target’s letter followed by a “>”.


A few sequences generated with that process are shown in Figure 3.


We trained a Free Transformer on this data for four different values of the free bits threshold _κ_, and
generated with the same random prompt three groups of sequences with each model, as pictured in
Figure 4. For each model, in the blue group, the noise _Z_ is sampled independently for each sequence,
whereas we sampled one _Z_ only for each of the green groups, used to generate all its sequences.


For very low values of the KL divergence, the model behaves like a vanilla model (Figure 4, middle left),
and when the value increases, the model encodes initially the position of the target alone in the latent
state (Figure 4, middle right), then encodes both the target position and the noise (Figure 4, bottom left),
and finally encodes the full sequence, resulting in incorrect generation (Figure 4, bottom right).


**4.2** **Baseline architectures**


For assessing performance on standard benchmarks we used decoder-only Transformers implemented in
the same Meta FAIR Transformer codebase as the one used by Copet et al. (2025) for the Computational


7


**K>!_________!_______!_______!____________!_______KKKKKKKK_________**

**C>___CCCCCCCC_________________!______!_____________!__!__!________**

**X>___________________!!_________!!___XX!XXXXX_____!_______________**

**R>!__RRRRRRRR_____________!__!_______________________________!____**

**P>!__!___________________________________________________PPPPPPPP_**

**L>_______!_!LLLLLLLL________!___________!!____________!___________**

**V>__!_________________!__!________VVVVVV!V________!_____!____!____**

**P>_________PPPPPPPP_____!________________!_______________________!**

**A>_______!___________!___________________________!_______AAAAAAA!_**

**P>____________________!____PPPPPP!P____!___________!_________!__!!**

**I>__________________________________________!_!__IIIIIIII_________**

**D>______!_!___________________________!_________!DDDDDDD__________**

**A>_____!___AAAAAAA!_______________!_________________!______!______**

**J>_______!_____!_________J!JJJJJJ_____________!___________________**


**Figure 3** The synthetic sequences of § 4.1 are of fixed length, with a “target” made of a random letter repeated 8
times at a random position, an i.i.d. noise of exclamation marks, and a prompt indicating the target’s letter.



**T>_________________________________TTTTTTTT_______________________**

**T>________________________________TTTTTTTT________________________**

**T>_________________________________TTTTTTTT_______________________**

**T>_____________________________________!TTTTTTTT__________________**

**T>_____________________________________________!_______TTTTTTTT___**


**T>_________________________________TTTTTTTT_______________________**

**T>_____________________________________________________TTTTTTTT___**

**T>______________________________________________________!TTTTTTTT_**

**T>___________________________!____________________________TTTTTTTT**

**T>_______________________________________________________TTTTTTTT_**


**T>_____________________________________________________TTTTTTTT___**

**T>_____________________________________________________TTTTTTTT___**

**T>___________________________________TTTTTTTT______!_____!____!___**

**T>_____________________________________________TTTTTTTT___________**

**T>__________________________________TTTTTTTT______________________**


_κ_ = log(2) _/_ 64 (1/64 bit)


**J>JJJJJJJ!____!_________!!__!_!_!__________!___________!___!__!___**

**J>_____!_____!______!______!_JJJJJJJJ______________________!______**

**J>___JJJ!JJJJ____________!__!___!_!__!_____!_____!!__!_____!___!__**

**J>__!___________JJJJJJJJ___________________!________!____!________**

**J>______!!___!!!_____________JJJJJJJJ!______!!!_!_!___!___________**


**J>_________JJJ!JJJJ__!______________!__________!!___!!_________!__**

**J>_________JJJ!JJJJ__!______________!______!____!__!!__________!__**

**J>_________JJ!JJJJJ__!_______!________!________!!__!!__________!__**

**J>_________JJJ!JJJJ__!________________!!____!!_!!____!_________!__**

**J>___!_____JJ!JJJJJ__!______________!_______!__!!_______!______!__**


**J>__JJJJJJJJ______!___________!____!_!______!_______!__!________!_**

**J>__JJJJJJJJ______!___________!____!_!________!__!__!__!________!_**

**J>_JJJJJJJJ_______!_______!________!_!______!_______!__!_______!__**

**J>_JJJJJJJJ_______!________________!_!________!__!____!!___!____!_**

**J>_JJJJJJJJ_______!___________!_____!_!_____!_______!__!_______!__**


_κ_ = log(2) (1 bit)



**F>_______________________________________________________FFFFFFFF_**

**F>___________________FFFFFFFF__________!__________!_______________**

**F>_________________FFFFFFFF________________________!____________!_**

**F>___________________________________FFFFFFFF__________________!__**

**F>____________________________________________!FFF!FFFF___________**


**F>_______________________!____________________________FFFFFFFF____**

**F>____________________________________________________FFFFFFFF____**

**F>____________________________________________________FFFFFFFF!___**

**F>___________________________________________________FFFFFFFF!____**

**F>_____________________________________________________FFFFFFFF___**


**F>_________________________FFFFFFFF!_________________!____________**

**F>__________!____________FF!FFFFF_________________________________**

**F>________________________FFFFFFFF___________________!____________**

**F>_______________________FFFFFFFF_______________!______!__________**

**F>_______________________FFFFFFFF______________________!__________**


_κ_ = log(2) _/_ 8 (1/8 bit)


**O>___________!!________!__!________________!_____!_______!______!!**

**O>____OOOOO______________________________________________________!**

**O>O!___O_!__!_!__!__!_OO____!!__OO_________________!!________!___!**

**O>_____!_____!_____________!_______________!_F___!!_!_______!_____**

**O>__OOOO!OO!___OO____!____O_!________________________O!____O_____!**


**O>_________OOOO________O__________!_____________________!!_!O____!**

**O>_________OO!O________O____O_____!_____________________!!!!O____!**

**O>_________OO!O________O____O_____!________________O____!__!O____!**

**O>_________OOOO________O____O_____!_____________________!!_!O____!**

**O>_________OOOO________O____O_____!______________________!_!O____!**


**O>__!___OO______________!___OO!O________O!O____________O_____O___!**

**O>O_!__OOO__________________OOOO________O!O____________O________!!**

**O>__!___OO__________________OO__________O!O____________O_____O____**

**O>__!___OO__________________OO__________O!O____O_______O_____O__!!**

**O>O_!__OOO_________!OO__!___OO__________O!O____________O_____O___!**


_κ_ = 8 log(2) (8 bits)



**Figure 4** Results with a Free Transformer trained on the synthetic sequences of § 4.1 for different prompts and free
bit thresholds. To investigate the information encoded in the latent tensor, we sample a _Z_ per sequence of a blue
box, and a _Z_ per green box. For very low values of the KL divergence, the model behaves like a vanilla model (top
left), and when the KL divergence increases, the model encodes initially the position of the target alone in the
latent state (top right), then encodes both the target position and the noise (bottom left), and finally encodes the
full sequence, resulting in incorrect generation (bottom right).


8


World Model. Those are well optimized models using the SwiGLU non-linearity (Shazeer, 2020), prenormalization with RMSNorm (Zhang et al., 2019), Rotary Positional Embedding (RoPE, Su et al. 2021),
and Group Query Attention (GQA, Ainslie et al. 2023). The vocabulary size is 2 [17] _≈_ 130 _k_ .


We used two sizes of models:


  - A 1.5B model, with 28 layers, weight tying between the embeddings and the logit readout, model
dimension 1536, 12 query heads, and 2 key-value heads. It is trained with 47B tokens, which requires
32 H100s for _≈_ 12 hours.


  - A 8B model with the structure of a Llama-3, which is 32 layers, model dimension 4096, 32 query
heads, and 8 key-value heads. It is trained with 200B tokens which requires 256 H100s for _≈_ 24
hours, or with 1T tokens, which takes 5 days.


We compare those baselines to the equivalent Free Transformers, which require one additional layer for
the encoder during training and KV cache pre-filling, resulting in a compute and memory overhead of
1 _/_ 28 _≈_ 3 _._ 6% for the 1.5B and 1 _/_ 32 _≈_ 3 _._ 1% for the 8B.


**4.3** **Setup and hyperparameters**


We kept our findings as clear as possible by avoiding other sources of performance improvement:


  - We stuck to the baseline architecture, optimizer, and learning rate schedule that were used to train
the baselines in FAIR’s framework, and did not optimize any hyperparameter for our setup.


  - We avoided any recipes for the VAE components, such as removing sampling in inference. We
followed the formal expressions rigorously.


  - We fixed _H_ to 16 so that the dimention of _Zt_ was comparable to the vocabulary size of 2 [17] .


We stress that the optimization hyperparameters were highly tuned for the baselines, and it is probable
that a combination of an encoder and a decoder has specific requirements that would greatly benefit from
an adapted training procedure.


**4.4** **Exploratory Results**


We ran a series of experiments to assess the general behavior of the Free Transformer, and to calibrate
the _κ_ threshold.


For any value of _κ_, the cross-entropy goes down regularly during training, with no more instability and
spikes than what happens with the baselines. The KL divergence rapidly goes under _κ_ and stays there.
When we compare the cross-entropies for various _κ_, they go down when _κ_ increases as expected, but the
values remain extremely close, with a difference of the order of 0 _._ 01 for a cross-entropy of _≈_ 2 for the 1.5B
and _≈_ 1 _._ 8 for the 8B.


For both sizes of models, setting _κ_ = 4 log 2, corresponding to 4 bits of information per token, resulted in
a collapse of the cross-entropy, indicating that the encoder found a way to channel fully the tokens to
predict, and resulting in a collapse of performance on the downstream tasks. It is noteworthy that the
baseline 8B model reaches during training a cross-entropy of 1 _._ 8 = 2 _._ 59 log(2), hence may explain why
allowing 2 bits does not collapse, while allowing 4 bits does.


The performance on downstream tasks are given in Table 1 for the 1.5B models, and Table 2 for the 8B
models, both for four different values of _κ_ corresponding to 1 _/_ 2 to 2 bits of information per token. Graphs
of performance during training are given in Appendix C in Figures 5 and 6.


We observe a substantial increase of performance on HumanEval+, MBPP, and GSM8K which are arguably
the benchmarks requiring some form of reasoning, and there also is a clear improvement for the 8B model
with 1/2 bit of KL divergence on MMLU and CSQA, which are multi-choice questions.


9


**1.5B models (47B tokens)**

**Free Transformer**
**Baseline**
1/4 bit 1/2 bit 1 bit 2 bits

Generative code/math


Multi-choice general knowledge / common sense


Multi-choice text understanding


Culture


**Table 1** Performance of 1.5B models trained on 47B tokens. The training procedure was tuned for the baseline
and kept unchanged, but the Free Transformers require 3 _._ 6% more compute and parameters for the encoder. See
Figure 5 in Appendix C for the performance during training.


**8B models (200B tokens)**

**Free Transformer**
**Baseline**
1/4 bit 1/2 bit 1 bit 2 bits

Generative code/math


Multi-choice general knowledge / common sense


Multi-choice text understanding


Culture


**Table 2** Performance of 8B models trained on 200B tokens. The training procedure was tuned for the baseline
and kept unchanged, but the Free Transformers require 3 _._ 1% more compute and parameters for the encoder. See
Figure 6 in Appendix C for the performance during training.


10


**8B models (1T tokens)**

|Col1|Final value|Col3|Average (last third)|Col5|
|---|---|---|---|---|
||**Baseline**|**Free Transformer**<br>1/2 bit|**Baseline**|**Free Transformer**<br>1/2 bit|



Generative code/math


Multi-choice general knowledge / common sense


Multi-choice text understanding


Culture


**Table 3** Performance of 8B models trained on 1T tokens. We also provide the average over the last third of the
iterations to mitigate the irregularity of the performance increase during training and get a more accurate estimate
of the relative improvement. The optimization hyperparameters were tuned for the baseline and kept unchanged,
but the Free Transformers require 3 _._ 1% more compute and parameters for the encoder. See Figure 7 in Appendix
C for the performance during training.


11


**4.5** **Results with 1T tokens training**


To measure improvement in a more realistic setting, closer to models actually used in real applications,
we trained 8B models on 1T tokens, which improves drastically the performance of both the baseline and
the Free Transformer.


Given the results with 200B tokens, we chose the value _κ_ = log(2) _/_ 2 corresponding to half a bit of
information per token at most.


The performance on downstream tasks are given in Table 3 and the corresponding graphs during training
in Figure 7 of Appendix C. We provide in the table the performance measured at the end of the training
as for the other configurations, but in addition we also give the average over the last third of the training.
We can observe on the graphs that the rate of improvement tend to be constant on this interval, which
justifies averaging to mitigate the performance fluctuations.


The key result is the boost of performance on HumanEval+, MBPP, GSM8K, MMLU and CSQA,
confirming what we observed in the smaller settings, and a greater stability on other tasks.

### **5 Previous work**


There have been several attempts at combining a VAE and a decoder Transformer, generally with a focus
on improving topic models and providing ways to guide the generation.


The OPTIMUS model (Li et al., 2020) combines a pre-trained BERT as text embedding / encoder, with a
GPT-2 playing the role of decoder, which are fine-tuned with a VAE-like loss.


The latent embedding _Z_ is computed thanks to a CLS token, that is by adding a token to the input and a
read-out to extract its embedding in the output. To modulate the GPT-2 generation with it, it is either (1)
concatenated as an additional token in every layer, or (2) added to the input token embeddings. Collapse
of the KL divergence is prevented during training with the free bits method (Kingma et al., 2016).


This approach allows for better guided text generation with GPT-2 and better generalization on low-data
languages with BERT.


Xie et al. (2021) extend OPTIMUS with a multi-objective loss, adding in particular the prediction of the
story topic, using the output of another model as ground truth, to obtain a better embedding space.


The CVAE proposed by Fang et al. (2021) combines two pre-trained GPT-2, one used as the encoder
without causal masking. The embedding _Z_ is an average of the encoder’s output, and the authors propose
three ways to modulate the decoder with linear images of it: (1) add it to each input token embedding, (2)
concatenate it to the Ks and Vs in every layer, (3) add it before the softmax. Experiments demonstrate
that this method allows controlling the generation without hurting the quality of the result.


AdaVAE (Tu et al., 2022) is similarly the combination of two pre-trained GPT-2, the first without causal
masking playing the role of the encoder. The latent embedding _Z_ is extracted from its output with a
slightly modified attention operator. It is then injected into the decoder by either concatenating an image
of it to the keys and values as in OPTIMUS, or before the softmax as in CVAE.

### **6 Conclusion**


The Free Transformer is a direct extension of a standard decoder Transformer, with the abstract structure
of a conditional VAE. It is implemented with a single additional non-causal Transformer block and requires
a few percent of computational and memory usage overhead.


Its structure makes it able to learn latent random variables unsupervised, and to condition its generative
process on them. In some ways, this approach aims at achieving in latent space with an autoencoder what
reasoning models do with chains-of-thought in token space and an RL procedure (DeepSeek-AI et al.,
2025). A combination of the two is, of course, promising.


12


The performance boost without tuning the optimization hyperparameters across multiple benchmarks and
two sizes of models, is a strong signal that the overall approach actually improves the inductive bias of
the vanilla Transformer.


Many properties and design choices should be explored. The performance curves during training are often
unstable, possibly due to the coupling of the optimization of the encoder and the decoder, and using
different optimization methods could be fruitful. The random embedding itself could take many forms,
and the one used in our implementation is arbitrary.


Finally, the behavior in larger scales, both in parameter count and dataset size, remains to be investigated.