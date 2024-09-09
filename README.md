![analytics image (flat)](https://raw.githubusercontent.com/vitr/google-analytics-beacon/master/static/badge-flat.gif)
![analytics](https://www.google-analytics.com/collect?v=1&cid=555&t=pageview&ec=repo&ea=open&dp=/red_basica/readme&dt=&tid=UA-4677001-16)

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
	<META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=utf-8">
	<META NAME="GENERATOR" CONTENT="LibreOffice 4.1.6.2 (Linux)">
	<META NAME="AUTHOR" CONTENT="LeoNazareth">
	<META NAME="CREATED" CONTENT="20160913;140200000000000">
	<META NAME="CHANGEDBY" CONTENT="LeoNazareth">
	<META NAME="CHANGED" CONTENT="20160916;123300000000000">
	<META NAME="AppVersion" CONTENT="14.0000">
	<META NAME="DocSecurity" CONTENT="0">
	<META NAME="HyperlinksChanged" CONTENT="false">
	<META NAME="LinksUpToDate" CONTENT="false">
	<META NAME="ScaleCrop" CONTENT="false">
	<META NAME="ShareDoc" CONTENT="false">
</HEAD>

<img src="https://github.com/leonazareth/sanibid_redbasica/blob/master/Images/Logo%20SaniBID%20RB_v.02..png"></P>


<BODY LANG="pt-BR" DIR="LTR">
<H1 CLASS="western">Apresentação</H1>
<P STYLE="margin-bottom: 0.14in"><BR><BR>
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
<FONT COLOR="#000000">
O saniBID RedBasica  é um software livre que tem como objetivo auxiliar no traçado 
e dimensionamento redes coletoras de esgoto, com ferramentas para projeto de sistemas do tipo condominial. 
Funciona como um complemento (Plug-in) para o software livre QGIS, de Sistema de Informações Geográficas.</P>
	
Em Setembro de 2021 foi lançada a versão 1.0 do plugin, que é suportado pelas versões do QGIS 3 em diante, mas recomenda-se utilizar sempre com a versão estável (LTR) atual, que pode ser consultada no site: https://qgis.org/en/site/. A versão 1.0 marca o fim da necessidade da utilização da planilha de dimensionamento baseada em Excel fornecida anteriormente, todos os cálculos nela realizados foram trazidos para uma aplicação dentro do próprio QGIS, o que torna o software 100% livre e de código aberto além de uma maior praticidade durante as etapas do projeto. Importante dizer que as funcionalidades de exportar a rede traçada para um arquivo .csv continuam no saniBID RedBasica, o que permite que os usuários que prefiram, continuem utilizando a <a href="https://github.com/sanihub/red_basica/blob/dev/saniBID_RedBasica_Planilha_Dimensionamento_PT_v191020.xlsm">planilha</a> de dimensionamento fornecida ou até mesmo uma planilha prória. </P>
	
O software foi desenvolvido originalmente para o Banco Interamericano de Desarrollo (BID), da Agencia Española de 
Cooperación Internacional para el Desarrollo (AECID) e a Latin America Investment Facility – European Union (LAIF) 
com a finalidade educativa e de promover o livre acesso a ferramentas modernas para o projeto de sistemas de esgoto 
e com funcionalidades adaptadas para o projeto de sistemas de esgoto do tipo condominial. </P>

<H1 CLASS="western" STYLE="line-height: 150%; page-break-before: always">
Funcionalidades</H1>
<P STYLE="margin-bottom: 0.14in; line-height: 150%"><BR><BR>
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
O complemento mescla funções básicas já presentes no QGIS
(ferramentas de desenho, georreferenciamento, dentre outras) com
outras funcionalidades criadas com a finalidade de facilitar e
automatizar o projeto de uma rede coletora de esgoto.</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
As ferramentas adicionadas ao QGIS pelo complemento são:</P>
<UL>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Criação de
	camadas vetoriais (shapes) pré-configuradas para elaboração do
	projeto;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Nomeação
	dos coletores;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Vinculação
	entre as camadas vetoriais e seus atributos;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Estilos e
	rótulos personalizados para cada camada;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Checagem de
	eventuais inconsistências do projeto;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Janelas de
	exibição dos atributos do trecho selecionado e outras informações
	do projeto;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Ferramenta de
	cálculos e dimensionamento das redes coletoras de esgoto diretamente
	dentro do QGIS, com todos os parâmetros de cálculos editáveis;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Importação
	dos resultados do cálculo hidráulico realizado de volta para o 
	traçado no QGIS;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Exportação
	dos resultados da rede dimensionada para o software EPA SWMM;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Exibição
	do resultado do dimensionamento na planta de projeto;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%"> Possibilidade de
	exportação de dados do traçado para cálculo hidráulico em outras
	planilhas ou softwares externos e posterior importação do resultado;</P>
</UL>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
O vínculo entre os módulos do QGIS e a aplicação de cálculos é feita de maneira simplificada
utilizando as ferramentas do plugin, caso o usuário queira exportar para o uso externo
(planilha ou software), isso é feito a partir das funções de exportação e importação de arquivo 
de texto separados por vírgula (“.csv”) contendo informações básicas para o dimensionamento, 
como: nomeação dos coletores, nomeação dos trechos, extensão de cada trecho,tipologia do traçado, 
cotas do terrenos, anotações auxiliares feitas pelo usuário durante o projeto, etc. </P>

Tanto a aplicação de cálculos interna quanto a planilha de cálculo fornecida (RedBasica) está baseada na norma brasileira de “Projeto de
redes coletoras de esgoto sanitário” (NBR 9649), incluindo o cálculo de tensão trativa. 
Os parâmetros de cálculo, contudo, podem ser ajustados livremente pelo usuário às 
características locais.</P>

<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
<BR><BR>
</P>
<H1 CLASS="western" STYLE="line-height: 150%">Instalação do Complemento</H1>
<P STYLE="margin-bottom: 0.14in; line-height: 150%"><BR><BR>
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
Para a instalação do complemento saniBID RedBasica o usuário deve:</P> 

<UL>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Descarregar o arquivo 
 disponibilizado no <a href="https://github.com/sanihub/red_basica/archive/refs/heads/dev.zip">LINK</a>;</P>
	<LI><P STYLE="margin-bottom: 0.14in; line-height: 150%">Utilizando o QGIS
  Versão 3.0 ou superior abrir o menu <b>Complementos>Instalar Complementos</b> e escolher a opção 
  <b>Install from Zip</b> e informar o local onde se encontra o instalador no seu computador, conforme a figura;</P> <img src="https://github.com/leonazareth/sanibid_redbasica/blob/master/Images/01%20Manual_Instalacao_Complemento_4.jpg" width=60% height=60%>

</P>
<H1 CLASS="western" STYLE="line-height: 150%">Tutoriais, cursos e manuais</H1>
<P STYLE="margin-bottom: 0.14in; line-height: 150%"><BR><BR>
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
Atualmente o manual completo para a versão 1.0 contendo a aplicação de cálculos no QGIS está em desenvolvimento,
além disso existe um curso disponibilizado através do <a href="https://www.youtube.com/playlist?list=PL1UvLzB7MU_YAU45sXd9zy0UOV3_hkMPH">canal do Youtube</a>
com tradução para Inglês, Espanhol e Francês, que também está sendo atualizado para incluir as novas funcionalidades.

<H1 CLASS="western" STYLE="line-height: 150%">Lista de Atributos</H1>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
<BR><BR>
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
O usuário pode escolher entre utilizar uma camada vetorial já
existente (com um traçado de rede já feito) ou inserir uma nova e
realizar seu traçado utilizando as ferramentas de desenho do QGIS. 
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
Os atributos padrão utilizados pelo plugin
estão listados com suas respectivas funções a seguir.</P>
<P STYLE="text-indent: -0.79in; margin-bottom: 0.14in; line-height: 150%">
Atributos da camada vetorial de trechos:</P>
<img src="https://github.com/leonazareth/sanibid_redbasica/blob/master/Images/Atributos_Trechos.png" width=60% height=60%></P>
Atributos da camada vetorial de dispositivos de inspeção (nós):</P>
<img src="https://github.com/leonazareth/sanibid_redbasica/blob/master/Images/Atributos_Nodes.png" width=60% height=60%></P>
<P STYLE="text-indent: -0.79in; margin-bottom: 0.14in; line-height: 150%">
Atributos da camada vetorial de unidades de contribuição:</P>
<img src="https://github.com/leonazareth/sanibid_redbasica/blob/master/Images/Unidades%20de%20Contribui%C3%A7%C3%A3o.png" width=60% height=60%></P>


<H1 CLASS="western" STYLE="line-height: 150%; page-break-before: always">
Colaboradores</H1>
<P STYLE="margin-bottom: 0.14in; line-height: 150%"><BR><BR>
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
Analista de Conceito: Leonardo Porto Nazareth</P>
</P>
<P STYLE="margin-bottom: 0.14in"><BR><BR>
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
Coordenação de desenvolvimento: Marta Fedz</P>
</P>
<P STYLE="margin-bottom: 0.14in"><BR><BR>
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
Desenvolvedores: Martin Dell' Oro e Federico Sanchez</P>
</P>
<P STYLE="margin-bottom: 0.14in"><BR><BR>
</P>
<P STYLE="text-indent: 0.39in; margin-bottom: 0.14in; line-height: 150%">
Cálculos e modelagem hidráulica: Leonardo Porto Nazareth e Pery Nazareth</P>


<H1 CLASS="western" STYLE="line-height: 150%; page-break-before: always">
Licença</H1>
<P STYLE="margin-bottom: 0.14in; line-height: 150%"><BR><BR>

O saniBID RedBasica é um software Copyleft. Possui código-fonte
livre para atualizações e melhorias, assegurando, porém, que os produtos
derivados da versão aqui disponível estejam licenciados sob
termos idênticos, sendo vetada qualquer tipo de comercialização dos
mesmos. Termos de Licença: GNU GPLv3

Para mais detalhes acesse o link de <a href="https://github.com/leonazareth/sanibid_redbasica/blob/master/LICENSE">LICENÇA</a> do plugin.

<H1 CLASS="western" STYLE="line-height: 150%; page-break-before: always">
Dúvidas e Sugestões</H1>
<P STYLE="margin-bottom: 0.14in; line-height: 150%"><BR><BR>
Qualquer dúvida, sugestão ou para reportar algum problema encontrado podem ser enviados para o e-mail: leonazareth@gmail.com

<H1 CLASS="western" STYLE="line-height: 150%; page-break-before: always">
Como Contribuir?</H1>
<P STYLE="margin-bottom: 0.14in; line-height: 150%"><BR><BR>
Se você tiver interesse em contribuir com o desenvolvimento do plugin, entre em contato pelo email: leonazareth@gmail.com
