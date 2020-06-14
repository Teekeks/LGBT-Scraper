
// credit: https://stackoverflow.com/a/50388154/6376756
function actionReddit(){
	var action_src = $("#uReddit").val();
	var urlLink = "/reddit/";
	urlLink = urlLink + action_src;
	window.location = urlLink;
	return false;
}

function actionTwitter(){
	var action_src = $("#uTwitter").val();
	var urlLink = "/twitter/";
	urlLink = urlLink + action_src;
	window.location = urlLink;
	return false;
}